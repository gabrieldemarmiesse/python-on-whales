from python_on_whales import docker

container = docker.run("ubuntu", ["sleep", "infinity"], detach=True)

def super_print(obj):
    print(f"type = {type(obj)}, value = {obj}")


super_print(container.id)
super_print(container.created)
super_print(container.path)
super_print(container.args)
super_print(container.state.status)
super_print(container.state.running)
super_print(container.state.paused)
super_print(container.state.restarting)
super_print(container.state.oom_killed)
a = eval("container.state.paused")
pass