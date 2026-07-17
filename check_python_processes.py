import psutil

for process_id in psutil.pids():
    p = psutil.Process(process_id)
    if p.name() == "python":
        cmd_line = p.cmdline()

        if 'http_server' not in cmd_line[1]:
            print(cmd_line)
