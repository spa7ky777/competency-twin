from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages: list[dict], chunk_size: int, overlap: int) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    out = []
    idx = 0
    for page in pages:
        text = page.get("text") or ""
        if len(text.strip()) < 20:
            continue
        pieces = splitter.split_text(text)
        for p in pieces:
            if len(p.strip()) < 20:
                continue
            out.append(
                {
                    "chunk_index": idx,
                    "text": p.strip(),
                    "page_number": page.get("page_number"),
                    "slide_number": page.get("slide_number"),
                    "char_count": len(p),
                }
            )
            idx += 1
    return out
