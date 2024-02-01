# sbt
A simple tool for executing [`sbatch`][sbatch], which is the job submission script of [slurm] workload manager.

## Features
- Simple templating for slumr batch file
  - Use [jinja] syntax for templating
- `matrix` for iterating over variables
- Variables can be specified via CLI

## Usage
Make a toml file that looks like this:

```bash
logdir = "logdir"

template = """
set -eo pipefail

python my_scipy.py --alpha={{ alpha }} --beta={{ beta }}
"""

[slurm_options]
cpus_per_task = 1
gres = [["gpu", 1]]
mail_type = ["END", "FAIL"]
mail_user = "me@example.com"
mem_per_cpu = { size = 64, unit = "G" }
nodes = 1
ntasks = 1
ntasks_per_node = 1
partition = "gpu"
time = { days = 1 }

[default_values]
alpha = 2e-5

[matrix]
alpha = [2e-5, 4e-5, 8e-5]
beta = [0.1, 0.01, 0.001]
```

then

```
sbt my-config.toml
```

Executing this command makes 9 (3x3) slurm batch files for each combination of alpha and beta, and submits them by `sbatch` command.

[jinja]: https://jinja.palletsprojects.com/en/3.1.x/
[slurm]: https://slurm.schedmd.com/
[sbatch]: https://slurm.schedmd.com/sbatch.html


