namespace OperaDemoWeb.Models
{
    public class UploadResponse
    {
        public string Status { get; set; } = string.Empty;
        public int FilesProcessed { get; set; }
        public int TotalChunks { get; set; }
        public string Message { get; set; } = string.Empty;
    }
}
