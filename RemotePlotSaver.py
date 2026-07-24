import plotly.io as pio
import plotly.graph_objects as go

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

import os

from pathlib import Path

import io

import json

import requests

from typing import List, Any, Optional, Dict, Union

# NOTE THIS BELONGS IN THE PRESENTATION_HELPER REPOSITORY
class RemotePlotSaver:
    def __init__(
            self,
            service_account_file: str = "service_account.json",
            scopes: Optional[List[str]] = None
    ) -> None:

        self.scopes = scopes or ["https://www.googleapis.com/auth/drive"]
        self.service_account_file = service_account_file
        self.service = self._init_drive_service()

        self.JSON_MIME = "application/json"
        self.FOLDER_MIME = "application/vnd.google-apps.folder"

    def _init_drive_service(self) -> Any:
        """Initializes Google Drive API client using service account credentials"""
        creds = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes = self.scopes
        )
        return build("drive", "v3", credentials=creds)

    # SINGLE FILE OPERATIONS

    def upload_file(
        self,
        file_path: Union[str, Path],
        parent_id: Optional[str] = None,
        make_public: bool = True
    ) -> str:
        """Uploads an existing local JSON file to Google Drive"""
        file_path = Path(file_path)
        file_metadata = {"name": file_path.name}

        if parent_id:
            file_metadata["parents"] = [parent_id]

        media = MediaFileUpload(str(file_path), mimetype=self.JSON_MIME)
        uploaded_file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fileds="id"
        ).execute()

        file_id = uploaded_file.get("id")
        if make_public:
            self._set_public_permission(file_id)

        return file_id
    
    # DIRECTORY MIRRORING
    
    def push_directory(
        self,
        local_dir: Union[str, Path],
        drive_root_folder_name: str
    ) -> str:
        """
        Recursively uploads a local directory tree of JSONs to Google Drive,
        preserving the exact subfolder hierarchy.
        """

        local_dir = Path(local_dir).resolve()

        if not local_dir.is_dir():
            raise ValueError(f"Local path '{local_dir}' is not a directory")

        # get/create root folder on Drive

        root_folder_id = self._get_or_create_folder(drive_root_folder_name)

        # keep track of relative subfolder paths

        folder_map: Dict[Path, str] = {Path("."): root_folder_id}

        for root, dirs, files in os.walk(local_dir):
            current_local_path = Path(root)
            rel_path = current_local_path.relative_to(local_dir)

            current_parent_id = folder_map[rel_path]

            # recreate subdirs on Drive
            for d in dirs:
                sub_rel_path = rel_path / d
                sub_folder_id = self._get_or_create_folder(
                    d, parent_id=current_parent_id
                )
                folder_map[sub_rel_path] = sub_folder_id

            # Upload JSON files in current folder
            for f in files:
                if f.endswith(".json"):
                    full_file_path = current_local_path / f
                    self.upload_file(
                        file_path = full_file_path,
                        parent_id = current_parent_id,
                        make_public=True
                    )

        return root_folder_id

    def pull_directory(
        self,
        drive_root_folder_name: str,
        local_target_dir: Union[str, Path]
    ) -> None:
        """
        Recursively downloadas a mirrored Google Drive folder structure back
        to a local target directory
        """

        local_target_dir = Path(local_target_dir).resolve()
        root_folder_id = self._find_folder_id(drive_root_folder_name)

        if not root_folder_id:
            raise FileNotFoundError(f"Drive folder '{drive_root_folder_name}' not found")

        self._pull_folder_recursive(root_folder_id, local_target_dir)

    def _pull_folder_recursive(
        self,
        drive_folder_id: str,
        local_current_dir: Path
    ) -> None:
        """Helper to recursively walk Drive folders and download contents."""

        local_current_dir.mkdir(parents=True, exist_ok=True)

        # query all items inside Drive folder
        query = f"'{drive_folder_id}' in parents and trashed = false"
        results = self.service.files().list(
            q=query, fields="files(id, name, mimeType)"
        ).execute()

        items = results.get("files", [])

        for item in items:
            item_id = item["id"]
            item_name = item["name"]
            mime_type = item["mimeType"]

            if mime_type == self.FOLDER_MIME:
                # recurse into subdir
                self._pull_folder_recursive(item_id, local_current_dir / item_name)
            elif item_name.endswith(".json"):
                # download file
                dest_path = local_current_dir / item_name
                self._download_file(item_id, dest_path)

    # HELPER UTILITIES

    def _set_public_permission(self, file_id: str) -> None:
        """Set a file, by file_id, to be publicly readable"""
        self.service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"}
        ).execute()

    def _find_folder_id(
        self, 
        folder_name:str, 
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """Searches for an existing folder (on Drive) by name and optonal parent"""

        query = f"name = '{folder_name}' and mimeType = '{self.FOLDER_MIME}' and trashed = false"
        
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.service.files().list(
            q=query, fields="files(id, name)"
        ).execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None

    def _get_or_create_folder(
        self, 
        folder_name: str, 
        parent_id: Optional[str] = None
    ) -> str:
        """Finds existing folder or creates a new one if missing."""

        existing_id = self._find_folder_id(folder_name, parent_id)
        if existing_id:
            return existing_id

        folder_metadata = {
            "name": folder_name,
            "mimeType": self.FOLDER_MIME
        }
        if parent_id:
            folder_metadata["parents"] = [parent_id]

        folder = self.service.files().create(
            body=folder_metadata, fields="id"
        ).execute()

        # grant public access 
        self._set_public_permission(folder.get("id"))

        return folder.get("id")

    def _download_file(self, file_id: str, dest_path: Path) -> None:
        request = self.service.files().get_media(fileId=file_id)
        with open(dest_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()        


if __name__ == "__main__":

    plot_saver = RemotePlotSaver()

    plot_saver.pull_directory(
        drive_root_folder_name="ab42",
        local_target_dir="./plots"
    )
