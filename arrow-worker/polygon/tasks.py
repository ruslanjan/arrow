import os

from arrow.celery import app
from polygon.sandbox import DefaultSandbox


# class Config:
#     def __init__(self,
#                  container_wall_time_limit,
#                  wall_time_limit,
#                  time_limit,
#                  memory_limit,
#                  files,
#                  run_command):
#         self.container_wall_time_limit = container_wall_time_limit
#         self.wall_time_limit = wall_time_limit
#         self.time_limit = time_limit
#         self.memory_limit = memory_limit
#         self.files = files
#         self.run_command = run_command


@app.task
def run_sandbox(config):
    app_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    container_wall_time_limit = 300    # 300 seconds

    sandbox = DefaultSandbox(
        container_wall_time_limit=container_wall_time_limit,
        wall_time_limit=config['wall_time_limit'],
        time_limit=config['time_limit'],
        memory_limit=config['memory_limit'],
        app_path=app_path,
        files=config['files'],
        run_command=config['run_command'])
    return sandbox.run
