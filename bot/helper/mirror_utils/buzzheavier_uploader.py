import asyncio
import json
import os

class BuzzheavierUploader:
    def __init__(self):
        pass
    
    async def buzzheavier_upload(self, item_path):
        file_name = os.path.basename(item_path)
        command = [
            "curl",
            "-#o", "-",
            "-T", f"{item_path}",
            f"https://w.buzzheavier.com/t/{file_name}",
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            try:
                response_data = json.loads(stdout.decode())
                if "id" in response_data:
                    hasil = {
                            "data": {
                                "code": f"{response_data['id']}",
                                "downloadPage": f"https://buzzheavier.com/f/{response_data['id']}",
                                "fileName": file_name,
                            },
                            "status": "ok"
                            }
                    return hasil
                else:
                    return {"status": "error", "message": f"Error saat upload ke buzzheavier, {stderr.decode()}"}
            except Exception as e:
                return {"status": "error", "message": f"Kesalahan saat mengakses server {e}"}
        else:
            return {"status": "error", "message": f"Terjadi kesalahan {stderr.decode()}"}