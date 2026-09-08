# 激活 conda base 环境
. "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
conda activate base
# 创建新环境（以3.12为例）
conda create -n py312 python=3.12 -y
conda activate py312
# 验证
python --version
# 自动激活conda base
如果想自动激活 conda base，在 .zprofile 里把那句话的 # 去掉即可。


# 生成依赖清单
pip freeze > requirements.txt

# 安装依赖
pip install -r requirements.txt

# 升级pip
pip install --upgrade pip

# 查看已安装的包
pip list

# 卸载包
pip uninstall pandas

执行pip install langchain报错  pip install langchain
Traceback (most recent call last):
  File "/Users/wwzhong/code/ai-agent/.venv/bin/pip", line 6, in <module>
    from pip._internal.cli.main import main
ModuleNotFoundError: No module named 'pip'
方法一：使用 ensurepip 模块修复（首选）
Python 内置了 ensurepip 模块，专门用来安装或修复 pip。
打开你的系统终端（Terminal），不要使用 PyCharm 内置的终端。
首先，激活你的出问题的虚拟环境：
```bash
source /Users/wwzhong/code/ai-agent/.venv/bin/activate
```
激活后，依次执行以下两个命令来修复并升级 pip：
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```
修复完成后，再尝试安装 langchain：
```bash
pip install langchain
```
