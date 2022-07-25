from sbatcher.options import Duration, Mem, Options, render


def test_render() -> None:
    options = Options(
        cpus_per_task=1,
        gres=[("gpu", 1)],
        job_name="myjob",
        mail_type=["END", "FAIL"],
        mail_user="yuji.kanagawa@oist.jp",
        mem_per_cpu=Mem(16, "G"),
        nodes=1,
        ntasks=1,
        ntasks_per_node=1,
        partition="gpu",
        time=Duration(1),
    )
    rendered = render(options)
    expected = r"""
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --job-name=myjob
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=yuji.kanagawa@oist.jp
#SBATCH --mem-per-cpu=16G
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --partition=gpu
#SBATCH --time=1-0:0
"""
    assert rendered == expected
