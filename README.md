<div align="center">

# Arknights-Toolkit

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![License](https://img.shields.io/github/license/RF-Tar-Railt/arknights-toolkit)](https://github.com/RF-Tar-Railt/arknights-toolkit/blob/master/LICENSE)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/arknights-toolkit)](https://img.shields.io/pypi/v/arknights-toolkit)

</div>

明日方舟(Arknights) 相关功能的整合库

现拥有如下功能：

- 抽卡
- 模拟十连
- 随机干员生成
- 公招链接生成
- 干员信息查询
- 猜干员游戏
- 抽卡结果查询

**欢迎 PR**

## 安装

```shell
pip install arknights-toolkit
```

```shell
pdm add arknights-toolkit
```

## 配置

抽卡分析功能依赖于sqlite数据库，请参考网络资源（如[菜鸟教程](https://www.runoob.com/sqlite/sqlite-installation.html)）安装SQLite数据库，无需控制数据库用户、创建数据库表等操作。但若为Windows环境，还需设置环境变量，无需配置数据库环境

使用前需要运行 initialize, 以下载图片资源:

```python
from arknights_toolkit import initialize

initialize(cover=True)
```

## 示例

```python
from arknights_toolkit.gacha import ArknightsGacha, GachaUser, simulate_image
from pathlib import Path
import asyncio


async def main():
    gacha = ArknightsGacha()
    user = GachaUser()
    data = gacha.gacha(user, 10)
    img = await simulate_image(data[0])
    with Path("example_sim.png").open("wb+") as f:
        f.write(img)

asyncio.run(main())
```

抽卡结果:

<img src="https://github.com/RF-Tar-Railt/arknights-toolkit/blob/master/example_sim.png" align="left" width="640" height="360" alt="抽卡结果">