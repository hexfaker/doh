
# doh

<div align="center">

[![Build status](https://github.com/hexfaker/doh/workflows/build/badge.svg?branch=master&event=push)](https://github.com/hexfaker/doh/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/doh.svg)](https://pypi.org/project/doh/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/hexfaker/doh/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/hexfaker/doh/blob/master/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%F0%9F%9A%80-semantic%20versions-informational.svg)](https://github.com/hexfaker/doh/releases)
[![License](https://img.shields.io/github/license/hexfaker/doh)](https://github.com/hexfaker/doh/blob/master/LICENSE)

Docker-based development environments. Think of it like conda envs or virtual envs on steroids.
</div> 

## Features

- Launch docker containers with strong defaults for interactive usage
  - workdir mounted by default
  - files created inside docker have correct ownership
  - dirs mounted and env vars set can be configured
  - Selected files from home dir can be propagated to fake home inside docker
- Run ssh server for remote development in containers without image modification, with docker on remote host support
- Launch jupyter kernels inside docker (either with vscode ssh development or with external jupyter server)

## Quick start
1) Ensure your python is at least 3.8
2) Install doh:
   * With [pipx](https://pypa.github.io/pipx/) (preferred, dependencies for cli tools installed with pipx are managed independently):
    ```shell
    pipx install 'git+https://github.com/hexfaker/doh.git'
    ```
   * To your existing virtualenv (your dependencies may conflict with doh's):
    ```shell
    pip install 'git+https://github.com/hexfaker/doh.git'
    ```
3) Cd into your project dir:
  ```shell
  mkdir -p my-simple-torch-project && cd my-simple-torch-project
  ```
3) Create `Dockerfile` in it
```dockerfile
# my-simple-torch-project/Dockerfile
FROM pytorch/pytorch:1.7.0-cuda11.0-cudnn8-devel
```
4) Create to-go doh config
```shell
doh init
```
5) Enjoy
```shell
doh sh # Spawns a shell inside container
doh ssh # Starts ssh server inside container, follow instructions to connect
doh kernel-install # Writes some configs for jupyterlab(notebook) that allows to run kernel inside container. Requires python and ipython to be present inside container
doh exec # For advanced usage, runs a single command inside container
```

## 🛡 License

[![License](https://img.shields.io/github/license/hexfaker/doh)](https://github.com/hexfaker/doh/blob/master/LICENSE)

This project is licensed under the terms of the `GNU GPL v3.0` license. See [LICENSE](https://github.com/hexfaker/doh/blob/master/LICENSE) for more details.

## 📃 Citation

```
@misc{doh,
  author = {Vsevolod Poletaev},
  title = {Docker-based development environments},
  year = {2021},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/hexfaker/doh}}
}
```

## Credits

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template).

https://github.com/kojiromike/parameter-expansion
