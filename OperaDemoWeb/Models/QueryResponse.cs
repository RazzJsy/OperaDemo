namespace OperaDemoWeb.Models
{
    public class QueryResponse
    {
        public string Question { get; set; } = string.Empty;
        public string Answer { get; set; } = string.Empty;
        public string? ValidationLevel { get; set; }
        public double? ConfidenceScore { get; set; }
        public List<SourceReference> Sources { get; set; } = new();
        public List<string> Warnings { get; set; } = new();
        public Dictionary<string, object> Metadata { get; set; } = new();
    }
}
