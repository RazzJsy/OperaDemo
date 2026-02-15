namespace OperaDemoWeb.Models
{
    public class HealthResponse
    {
        public string Status { get; set; } = string.Empty;
        public bool PipelineReady { get; set; }
        public bool DocumentsLoaded { get; set; }
        public bool LlmAvailable { get; set; }
    }
}
