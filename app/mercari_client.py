"""占位模块：个人卖家版不使用 Mercari Shops 官方 API。

上架流程由 Automa 浏览器扩展完成（见 README_项目要求.md 第 9 节），
本文件仅保留占位，不发起任何真实 API 调用。
"""


class MercariClient:
    """占位类。个人卖家版无需实例化。"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.enabled = False

    def create_listing(self, **kwargs):
        raise NotImplementedError(
            "个人卖家版不使用官方 API 自动上架，请使用 Automa 网页自动化（人工确认后提交）。"
        )
