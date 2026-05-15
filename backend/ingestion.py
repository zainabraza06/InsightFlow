import io
import re
import csv
import logging
from datetime import datetime

import fitz  # PyMuPDF
import httpx

logging.basicConfig(level=logging.INFO, format="[NEXUS] %(message)s")
logger = logging.getLogger("nexus.ingestion")


class IngestionEngine:

    def process_pdf(self, file_bytes: bytes) -> dict:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
            logger.info(f"PDF processed — {len(full_text.split())} words extracted")
            return {
                "source_type": "pdf",
                "content": full_text,
                "word_count": len(full_text.split()),
                "timestamp": datetime.utcnow().isoformat(),
                "credibility_base": 0.85,
            }
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                "source_type": "pdf",
                "content": "PDF_PARSE_FAILED",
                "credibility_base": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def process_url(self, url: str) -> dict:
        try:
            response = httpx.get(url, timeout=10, follow_redirects=True)
            html = response.text
            cleaned = re.sub(r"<[^>]+>", " ", html)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            logger.info(f"URL processed — {url[:60]} — {len(cleaned)} chars")
            return {
                "source_type": "url",
                "content": cleaned[:3000],
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
                "credibility_base": 0.70,
            }
        except Exception as e:
            logger.warning(
                f"URL source excluded — fetch failed, credibility scored 0.0. Pipeline continues with remaining sources. Error: {e}"
            )
            return {
                "source_type": "url",
                "content": "URL_FETCH_FAILED",
                "credibility_base": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def process_csv(self, csv_text: str) -> dict:
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
            fieldnames = reader.fieldnames or []

            temporal_keywords = {"date", "month", "week", "day"}
            has_temporal = any(
                any(kw in col.lower() for kw in temporal_keywords)
                for col in fieldnames
            )

            lines = [f"Columns: {', '.join(fieldnames)}"]
            for row in rows:
                line = " | ".join(f"{k}: {v}" for k, v in row.items())
                lines.append(line)
            summary = "\n".join(lines)

            logger.info(f"CSV processed — {len(rows)} rows, temporal={has_temporal}")
            return {
                "source_type": "csv",
                "content": summary,
                "has_temporal": has_temporal,
                "row_count": len(rows),
                "timestamp": datetime.utcnow().isoformat(),
                "credibility_base": 0.90,
            }
        except Exception as e:
            logger.error(f"CSV processing failed: {e}")
            return {
                "source_type": "csv",
                "content": "CSV_PARSE_FAILED",
                "credibility_base": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def process_text(self, text: str) -> dict:
        logger.info(f"Text processed — {len(text.split())} words")
        return {
            "source_type": "text",
            "content": text,
            "timestamp": datetime.utcnow().isoformat(),
            "credibility_base": 0.65,
        }

    def process_mock_feed(self, topic: str) -> dict:
        topic_lower = topic.lower()
        if "fuel" in topic_lower:
            feed_text = "[LIVE 14:32] Petroleum dealers report pump queues averaging 45 min across 3 cities. Spot price +8% vs morning rate."
        elif "sales" in topic_lower:
            feed_text = "[LIVE 14:32] POS terminals show 40% volume drop vs same hour last week in Lahore region. 3 major outlets reporting zero transactions."
        elif "supply" in topic_lower:
            feed_text = "[LIVE 14:32] Port authority confirms 14 containers held at Karachi customs. Estimated clearance delay: 72 hours."
        else:
            feed_text = "[LIVE 14:32] Anomalous activity detected across monitored indicators. Variance exceeds 2-sigma threshold."

        logger.info(f"Mock feed processed — topic: {topic}")
        return {
            "source_type": "realtime_feed",
            "content": feed_text,
            "timestamp": datetime.utcnow().isoformat(),
            "credibility_base": 0.60,
        }

    def ingest_all(self, sources: list) -> list:
        results = []
        for src in sources:
            src_type = src.get("type", "")
            data = src.get("data", "")
            try:
                if src_type == "pdf":
                    result = self.process_pdf(data)
                elif src_type == "url":
                    result = self.process_url(data)
                elif src_type == "csv":
                    result = self.process_csv(data)
                elif src_type == "text":
                    result = self.process_text(data)
                elif src_type == "feed":
                    result = self.process_mock_feed(data)
                else:
                    logger.warning(f"Unknown source type: {src_type} — skipping")
                    continue
                results.append(result)
                logger.info(f"Source ingested: {src_type} — credibility_base={result.get('credibility_base', 0)}")
            except Exception as e:
                logger.error(f"Source {src_type} failed: {e}")
        return results
