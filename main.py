from pathlib import Path
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


EXTENSIONS = {
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.eps', '.raw', '.cr2', '.nef'],
    'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mxf', '.mts', '.vob'],
    'documents': ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.ppt', '.pptx', '.csv', '.odt', '.rtf', '.epub', '.odf'],
    'music': ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.midi', '.aac', '.wma', '.alac', '.amr'],
    'programs': ['.exe', '.msi', '.app', '.bat', '.cmd', '.py', '.jar', '.dll', '.sh'],
    'compressed': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
    'databases': ['.mdf', '.ndf', '.ldf', '.frm', '.ibd', '.myd', '.myi', '.sql', '.dump', '.conf', '.sqlite', '.sqlite3', '.db', '.db3', '.dbf', '.ctl', '.log', '.mdb', '.accdb', '.bkp', '.fdb', '.dbs', '.idx', '.hdb', '.bak'],
    'others': []
}

TEMPORARY_EXTENSIONS = {'.crdownload', '.part', '.tmp'}


def generate_extension_dictionary() -> dict:
    """Auxiliar function that takes the EXTENSIONS dictionary and creates
    a new dictionary where each extension is associated with a folder name
    """
    extension_decitionary = {}
    for category, lst in EXTENSIONS.items():
        for file_ext in lst:
            extension_decitionary[file_ext] = category
    return extension_decitionary


class FolderManager:
    """ Main class of the script. It's job is to take the folder that the user 
    wants to organize, runs the file extensions through the file extension dictionary
    (see generate_extension_dictionary function). Then it moves the file to a directory 
    according to its file extension
    """

    def __init__(self, parent_folder: Path):
        self.parent_folder = parent_folder
        self.extension_dict = generate_extension_dictionary()

    def move_file(self, file: Path, extension: Path) -> None:
        """
            In here is where the file, as a Path object, is moved to a folder according to
            its extension type. First it checks that it exists, if not, then it creates 
            the folder. It also controls whether the file already exists in the folder. If it does,
            then it creates a "copy" (hence the counter variable) of the file path. if many instances
            of the same file are inside the folder (say file.f, file(1).f,...) then it iterates
            until it creates a unique file extension. 
        """
        try:
            if not extension.exists():
                extension.mkdir(parents=True, exist_ok=True)
            destination = extension / file.name
            count = 1

            while destination.exists():
                destination = extension / f"{file.stem}({count}){file.suffix}"
                count += 1
            shutil.move(src=file, dst=destination)

        except Exception as e:
            print(f"Cannot move files or create sub folders: {e}")

    def orgnanize_files(self) -> None:
        """
            This function iterates through the files inside the folder
            that the user wants to organize. If the element is a file and does not
            begin with '.', then it selects from the extensions directory a category
            and creates a file path. After this it procedes to the move_file function.
            if there are no files in the parent folder, then it prints 'No files to organize'
        """
        has_files = False
        for file in self.parent_folder.iterdir():
            if file.is_file() and not file.name.startswith('.'):
                has_files = True
                extension = self.extension_dict.get(file.suffix, 'others')
                extension_file_path = file.parent.joinpath(extension)
                self.move_file(file, extension_file_path)
        if not has_files:
            print("No files to organize")


class DownloadEventHandler(FileSystemEventHandler):
    """
        This class has the purpose of monotoring the Downloads direcotry and detecting 
        when a file is done downloading before it is moved to its corresponding 
        folder
    """

    def __init__(self, folder_manager: FolderManager, stabilty_float: float = 1.0, delay: float = 5.0):
        self.folder_manager = folder_manager
        self.stability_float = stabilty_float
        self.delay = delay
        self.last_event_time = time.time()

    # def on_modified(self, event):
    #     if not event.is_directory:
    #         print("Moving files")
    #         self.folder_manager.orgnanize_files()

    def is_file_stable(self, file_path: Path) -> bool:
        """
            Function that determines whether a file is ready to be moved or if
            is it still downloading 
        """
        try:
            initial_size = file_path.stat().st_size
            time.sleep(self.stability_float)
            final_size = file_path.stat().st_size
            return final_size == initial_size
        except FileNotFoundError:
            return False

    def on_created(self, event):
        """
            Main function that calls the 'organize_files' method from
            the FolderManager class. If the file path is stable, then
            it moves the file to its corresponding folder
        """
        if not event.is_directory:
            file_path = Path(event.src_path)

            if file_path.suffix in TEMPORARY_EXTENSIONS:
                print(f"ingnoring {file_path.name} file")
                return

            if self.is_file_stable(file_path):
                time_since_last_event = time.time() - self.last_event_time
                self.last_event_time = time.time()

                if time_since_last_event > self.delay:
                    print("Download complete")
                    time.sleep(self.delay)
                    self.folder_manager.orgnanize_files()

            else:
                print("File incomplete or still downloading")


if __name__ == "__main__":
    home_path = str(Path.home())
    download_path = Path(f"{home_path}/Downloads")

    if not download_path.exists():
        print("No file path found")
    else:

        folder_manager = FolderManager(download_path)

        event_handler = DownloadEventHandler(folder_manager)

        observer = Observer()
        observer.schedule(event_handler, download_path, recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
