namespace OperaDemoWeb.Models
{
    public class StatsResponse
    {
        public bool DocumentsLoaded { get; set; }
        public RetrieverStats Retriever { get; set; } = new();
        public string LlmModel { get; set; } = string.Empty;
        public int ChunkSize { get; set; }
        public int TopKRetrieval { get; set; }
    }
}
