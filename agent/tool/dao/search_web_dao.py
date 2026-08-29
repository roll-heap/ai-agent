from duckduckgo_search import DDGS

from agent.tool.model.seatch_web_model import SearchWebModel


class SearchWebDao:
    @staticmethod
    def search_web(keywords: str, max_results: int|None = 5) -> list:
        result = []
        with DDGS() as ddgs:
            for r in ddgs.text(keywords = keywords, max_results = max_results):
                title = r.get("title", "无标题")
                href = r.get("href", "")
                body = r.get("body", "")
                search_model = SearchWebModel(title=title, href=href, body=body)
                result.append(search_model)

        return result