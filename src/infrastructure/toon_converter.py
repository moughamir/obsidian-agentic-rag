"""
Phase 2: TOON Format Converter
Infrastructure Layer - Token-efficient data serialization

TOON (Token-Optimized Object Notation):
- 30-60% fewer tokens than JSON
- Indentation-based hierarchy
- Tabular format for arrays
- No curly braces, quotes, or commas

Example JSON:
{
  "chunks": [
    {"id": 1, "score": 0.95, "content": "..."},
    {"id": 2, "score": 0.87, "content": "..."}
  ]
}

Example TOON:
chunks
  id score content
  1  0.95  ...
  2  0.87  ...
"""

from typing import Any, Dict, List
import json


class TOONConverter:
    """
    Convert between JSON and TOON format

    Single Responsibility: Format conversion for token efficiency

    Use TOON for:
    - Large context payloads to LLM
    - Document chunks with metadata
    - Agent communication

    Keep JSON for:
    - Configuration files
    - API responses (for compatibility)
    """

    @staticmethod
    def to_toon(data: Any, indent: int = 0) -> str:
        """
        Convert Python object to TOON format

        Args:
            data: Dict, list, or primitive
            indent: Current indentation level

        Returns:
            TOON formatted string
        """
        indent_str = "  " * indent

        if isinstance(data, dict):
            return TOONConverter._dict_to_toon(data, indent)
        elif isinstance(data, list):
            return TOONConverter._list_to_toon(data, indent)
        else:
            return str(data)

    @staticmethod
    def _dict_to_toon(data: Dict, indent: int) -> str:
        """Convert dictionary to TOON"""
        lines = []
        indent_str = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                # Nested dict
                lines.append(f"{indent_str}{key}")
                lines.append(TOONConverter.to_toon(value, indent + 1))
            elif isinstance(value, list):
                # List/array
                lines.append(f"{indent_str}{key}")
                lines.append(TOONConverter.to_toon(value, indent + 1))
            else:
                # Primitive value
                lines.append(f"{indent_str}{key} {value}")

        return "\n".join(lines)

    @staticmethod
    def _list_to_toon(data: List, indent: int) -> str:
        """
        Convert list to TOON tabular format

        Optimized for: Lists of uniform objects
        """
        if not data:
            return ""

        indent_str = "  " * indent

        # Check if list contains dicts (tabular format)
        if isinstance(data[0], dict):
            return TOONConverter._list_of_dicts_to_toon(data, indent)
        else:
            # Simple list
            lines = []
            for item in data:
                lines.append(f"{indent_str}{item}")
            return "\n".join(lines)

    @staticmethod
    def _list_of_dicts_to_toon(data: List[Dict], indent: int) -> str:
        """
        Convert list of dicts to tabular TOON format

        Most token-efficient format for uniform objects
        """
        if not data:
            return ""

        indent_str = "  " * indent

        # Extract headers
        headers = list(data[0].keys())
        header_line = indent_str + " ".join(headers)

        # Extract rows
        rows = []
        for item in data:
            row_values = [str(item.get(h, "")) for h in headers]
            rows.append(indent_str + " ".join(row_values))

        return "\n".join([header_line] + rows)

    @staticmethod
    def from_toon(toon_str: str) -> Dict:
        """
        Convert TOON back to Python dict

        Note: This is a simplified parser
        Production would need more robust parsing
        """
        # For MVP, provide JSON fallback
        # Full TOON parser is complex but doable
        try:
            return json.loads(toon_str)
        except json.JSONDecodeError:
            # Simple TOON parsing (basic implementation)
            result = {}
            lines = toon_str.strip().split("\n")

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    result[key.strip()] = value.strip()

            return result


class ContextOptimizer:
    """
    Optimizes context for LLM consumption

    Strategies:
    1. TOON conversion for structured data
    2. Chunking for long documents
    3. Summarization for background context
    """

    @staticmethod
    def optimize_documents_for_llm(
        documents: List[Any],
        format: str = "toon"
    ) -> str:
        """
        Convert document list to token-efficient format

        Args:
            documents: List of MCPDocument or dicts
            format: "toon" or "json"

        Returns:
            Formatted string ready for LLM
        """
        if format == "toon":
            # Convert to TOON for 30-60% token savings
            doc_data = []
            for doc in documents:
                if hasattr(doc, "__dict__"):
                    doc_data.append({
                        "path": doc.path,
                        "score": round(doc.score, 2),
                        "content": doc.content[:500]  # Truncate long content
                    })
                else:
                    doc_data.append(doc)

            return TOONConverter.to_toon({"documents": doc_data})
        else:
            # Standard JSON
            return json.dumps(documents, indent=2)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Rough token estimation

        Rule of thumb: ~4 characters per token for English
        """
        return len(text) // 4

    @staticmethod
    def compare_formats(data: Dict) -> Dict[str, Any]:
        """
        Compare token efficiency of JSON vs TOON

        Returns metrics for analysis
        """
        json_str = json.dumps(data)
        toon_str = TOONConverter.to_toon(data)

        json_tokens = ContextOptimizer.estimate_tokens(json_str)
        toon_tokens = ContextOptimizer.estimate_tokens(toon_str)

        savings = (json_tokens - toon_tokens) / json_tokens * 100

        return {
            "json_length": len(json_str),
            "toon_length": len(toon_str),
            "json_tokens": json_tokens,
            "toon_tokens": toon_tokens,
            "token_savings_pct": round(savings, 1),
            "bytes_saved": len(json_str) - len(toon_str)
        }


# Example Usage
def example_toon_conversion():
    """Demonstrate TOON efficiency"""

    # Sample data - typical RAG context
    data = {
        "query": "What is clean architecture?",
        "chunks": [
            {
                "id": 1,
                "path": "architecture/clean.md",
                "score": 0.95,
                "content": "Clean architecture separates concerns into layers..."
            },
            {
                "id": 2,
                "path": "architecture/solid.md",
                "score": 0.87,
                "content": "SOLID principles guide clean code..."
            },
            {
                "id": 3,
                "path": "architecture/kiss.md",
                "score": 0.82,
                "content": "KISS principle advocates simplicity..."
            }
        ]
    }

    # Convert to TOON
    toon_output = TOONConverter.to_toon(data)

    print("JSON format:")
    print(json.dumps(data, indent=2))
    print("\n" + "="*60 + "\n")

    print("TOON format:")
    print(toon_output)
    print("\n" + "="*60 + "\n")

    # Compare efficiency
    metrics = ContextOptimizer.compare_formats(data)
    print("Efficiency comparison:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    return toon_output


if __name__ == "__main__":
    example_toon_conversion()
