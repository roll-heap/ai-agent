# conda
Conda 的常用命令主要围绕环境管理和包管理两大核心功能，以下按类别进行了整理。
你可以随时在命令后加上 --help 来查看更详细的用法，例如 conda create --help。

## 1、环境管理
环境管理是 Conda 最核心的功能，可以创建相互隔离的Python环境，避免不同项目间的依赖冲突。</br>

| 任务       | 命令                                                          | 示例                                              |
|------------|---------------------------------------------------------------|---------------------------------------------------|
| 创建环境   | conda create -n <env_name> python=<version>                   | conda create -n myenv python=3.9                  |
| 克隆环境   | conda create --clone <old_env> -n <new_env>                   | conda create --clone myenv -n myenv_backup        |
| 激活环境   | conda activate <env_name>                                     | conda activate myenv                              |
| 退出环境   | conda deactivate                                              | conda deactivate                                  |
| 列出环境   | conda env list                                                | conda env list                                    |
| 删除环境   | conda remove -n <env_name> --all                              | conda remove -n myenv --all                       |
| 重命名环境 | conda rename -n <old_name> <new_name>                         | conda rename -n myenv myenv_new                   |
| 导出环境   | conda env export > environment.yml                            | conda env export > environment.yml                |
| 导出环境   | conda env export --from-history > environment.yml(跨平台兼容) | conda env export --from-history > environment.yml |
| 导入环境   | conda env create -f environment.yml                           | conda env create -f environment.yml               |
## 2、包管理
在激活目标环境后，可以使用以下命令管理该环境中的包。

| 任务           | 命令                                   | 示例                                    |
|----------------|----------------------------------------|-----------------------------------------|
| 安装包         | conda install <package_name>           | conda install numpy                     |
| 安装特定版本   | conda install <package_name>=<version> | conda install numpy=1.21                |
| 安装多个包     | conda install <pkg1> <pkg2> ...        | conda install numpy pandas matplotlib   |
| 从特定频道安装 | conda install -c <channel> <package>   | conda install -c conda-forge matplotlib |
| 更新包         | conda update <package_name>            | conda update numpy                      |
| 更新所有包     | conda update --all                     | conda update --all                      |
| 移除包         | conda remove <package_name>            | conda remove numpy                      |
| 搜索包         | conda search <search_term>             | conda search numpy                      |
| 列出已安装包   | conda list                             | conda list                              |
## 3、配置与管理
这些命令用于管理 Conda 自身及其配置。

| 任务       | 命令                                         | 示例                                    |
|------------|----------------------------------------------|-----------------------------------------|
| 查看版本   | conda --version                              | conda --version                         |
| 更新 Conda | conda update -n base conda                   | conda update -n base conda              |
| 查看帮助   | conda --help                                 | conda --help                            |
| 查看配置   | conda config --show                          | conda config --show                     |
| 添加频道   | conda config --add channels <channel_url>    | conda config --add channels conda-forge |
| 查看频道   | conda config --show channels                 | conda config --show channels            |
| 移除频道   | conda config --remove channels <channel_url> | conda config --remove channels defaults |
## 4、清理缓存
随着使用时间增长，Conda 会积累大量缓存，可以通过以下命令清理。

| 任务         | 命令              | 示例              |
|--------------|-------------------|-------------------|
| 清理所有缓存 | conda clean --all | conda clean --all |
| 清理无用包   | conda clean -p    | conda clean -p    |