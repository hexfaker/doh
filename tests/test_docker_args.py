from doh.docker import docker_run_args_from_project

# def test_minimal_config_args(context):
#
#
#     args = docker_run_args_from_project(context)
#
#     hostname_idx = args.index("--hostname")
#     assert args[hostname_idx + 1] == context.environment_id
#
#     if context.config.workdir_from_host:
#         workdir_arg_idx = args.index("--workdir")
#         assert args[workdir_arg_idx + 1] == str(context.project_dir)
#
#     args.index("--ipc=host")
#     args.index("--pid=host")
