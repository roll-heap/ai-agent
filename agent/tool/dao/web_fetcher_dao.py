import requests
from bs4 import BeautifulSoup

from exception.agent_exception import AgentException


class WebFetcherDao:
    @staticmethod
    def web_fetcher(url: str, max_length:int=2000) -> str:
        """
        抓取网页内容，返回纯文本（限制长度）
        """
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            response.encoding="utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)

            # 限制长度，放在模型上下文过长
            if len(text) > max_length:
                text = (text[:max_length] + "...\n[内容已截断]")

            return f"网页 {url} 的内容：\n{text}"
        except requests.exceptions.Timeout:
            raise AgentException("网页请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            raise AgentException("网络连接失败，请检查 URL")
        except requests.exceptions.HTTPError as e:
            raise AgentException(f"网页请求失败：{str(e)}")
        except Exception as e:
            raise AgentException(f"抓取失败，失败原因：{str(e)}")