namespace OperaDemoWeb.Models
{
    public class SourceReference
    {
        public string Text { get; set; } = string.Empty;
        public string Source { get; set; } = string.Empty;
        public int Page { get; set; }
        public double CombinedScore { get; set; }
        public double Bm25Score { get; set; }
        public double DenseScore { get; set; }
    }
}
