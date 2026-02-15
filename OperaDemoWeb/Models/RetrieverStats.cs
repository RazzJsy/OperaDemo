namespace OperaDemoWeb.Models
{
    public class RetrieverStats
    {
        public int TotalChunks { get; set; }
        public int EmbeddingDimensions { get; set; }
        public bool Bm25Indexed { get; set; }
        public int UniqueSources { get; set; }
    }
}
