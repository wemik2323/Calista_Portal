import cups
from typing import List, Dict, Optional

class CUPSClient:
    
    def __init__(self):
        self.conn = None
        self._connect()
 

    def _connect(self):
        try:
            self.conn = cups.Connection()

        except Exception as e:
            print(f"Ошибка подключения к CUPS: {e}")
            self.conn = None
    
    def get_printers(self) -> List[Dict]:
 
        if not self.conn:
            return []
        
        try:
            printers = self.conn.getPrinters()
            
            
            result = []



            for name, info in printers.items():
                result.append(
                    {
                        'name': name,
                        'model': info.get('printer-make-and-model', 'Неизвестная модель'),
                        'status': info.get('printer-state', 'unknown'),
                        'location': info.get('printer-location', ''),
                        'is_default': info.get('printer-is-default', False)
                    }
                )
            

            return result


        except Exception as e:
            print(f"Ошибка получения принтеров: {e}")
            return []

    
    def print_file(
            self, 
            printer_name: str, 
            filepath: str, 
            title: str,
            paper_size: str = "A4",
            orientation: str = "portrait",
            scaling: str = "auto",
    ) -> Optional[int]:
 
        if not self.conn:
            raise Exception("Нет подключения к CUPS")
        
        try:
            printers = self.conn.getPrinters()
            if printer_name not in printers:
                raise ValueError(f"Принтер '{printer_name}' не найден")


            options = {
                "media": paper_size,
            }

            if orientation == "portrait":
                options["orientation-requested"] = "3"
            elif orientation == "landscape":
                options["orientation-requested"] = "4"

            if scaling == "auto":
                options["print-scaling"] = "auto"
            elif scaling == "fill":
                options["print-scaling"] = "fill"
            
            return self.conn.printFile(
                printer_name,
                filepath,
                title,
                options,
            )
            
        except cups.IPPError as e:
            raise Exception(f"Ошибка CUPS: {str(e)}")
    


    def get_job_status(self, job_id: int) -> Dict:
     
        if not self.conn:
            return {'status': 'unknown'}


        try:
            jobs = self.conn.getJobs()


            if job_id not in jobs:
                return { "status": "not_found",}


            job = jobs[job_id]

            
            state = job.get(
                "job-state",
                "unknown",
            )

            return {
                "status": state,
                "printer": job.get(
                    "printer-uri",
                    "",
                ),
                "title": job.get(
                    "job-name",
                    "",
                ),
            }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}
