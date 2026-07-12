import os
import shutil
from typing import Any

class FileBackupTool:
    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        file_path = payload.get("path")
        backup_dir = "backups"
        
        # 1. Validation
        if not file_path or not os.path.exists(file_path):
            return {"status": "error", "message": f"File {file_path} not found."}
        
        # 2. Ensure backup directory exists
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # 3. Perform backup
        filename = os.path.basename(file_path)
        destination = os.path.join(backup_dir, f"{filename}.bak")
        shutil.copy2(file_path, destination)
        
        return {"status": "success", "message": f"Backup created at {destination}"}

TOOL_REGISTRY = {
    "local_file_backup": FileBackupTool(),
}