import os
from typing import Optional
import lightning as L
import subprocess
import shlex
from lightning_app.utilities.network import find_free_network_port

# sudo apt-get install net-tools  
# sudo apt-get install nmap
# sudo apt-get install screen
# sudo apt-get install iputils-ping

PG_INSTALL = """
sudo apt-get update
sudo apt-get install vim
sudo apt-get install postgresql
""".split('\n')


VSC_INSTALL = """
curl -fsSL https://code-server.dev/install.sh | sh
""".split('\n')

class CustomBuildConfig(L.BuildConfig):
    def build_commands(self):
        return VSC_INSTALL + PG_INSTALL

class PostgreSQL(L.LightningWork):
    def __init__(self, cloud_compute: Optional[L.CloudCompute] = None):
        super().__init__(cloud_compute=cloud_compute, cloud_build_config=CustomBuildConfig(), parallel=True)
        self.pgsql_url = None
    
    def run(self):
        # Change VSCode Server Port
        # https://www.jamescoyle.net/how-to/3019-how-to-change-the-listening-port-for-postgresql-database
        free_port = find_free_network_port()
        print(free_port)
        cmd1 = ['sed -i "s/port = 5432/port = {free_port}/g" /etc/postgresql/12/main/postgresql.conf"']
        #cmd2 = [sed -i "s/listen_addresses = 'localhost'/listen_addresses='*'"]
        cmd2 = ["service postgresql start"]

        with open(f"/home/zeus/psql_{free_port}", "w") as f:
            proc = subprocess.Popen(
                shlex.split(cmd1[0]),
                bufsize=0,
                close_fds=True,
                stdout=f,
                stderr=f,
            )
        
        with open(f"/home/zeus/vscode_server_{self.port}", "w") as f:
            proc = subprocess.Popen(
                shlex.split(f"code-server --bind-addr '{self.host}:{self.port}' --auth none"),
                bufsize=0,
                close_fds=True,
                stdout=f,
                stderr=f,
            )

class RootFlow(L.LightningFlow):
    def __init__(self) -> None:
        super().__init__()
        self.pg_work = PostgreSQL(cloud_compute=L.CloudCompute(os.getenv("COMPUTE", "cpu-small")))

    def run(self):
        self.pg_work.run()
    
    def configure_layout(self):
        return [{'name': "VSCode", 'content': self.pg_work}]

app = L.LightningApp(RootFlow())