namespace OperaDemoWeb.Services
{
    using OperaDemoWeb.Models;
    using Microsoft.AspNetCore.Components.Forms;
    using System.Text.Json;

    public class ApiService(HttpClient httpClient, ILogger<ApiService> logger)
    {
        private readonly HttpClient _httpClient = httpClient;

        private readonly ILogger<ApiService> _logger = logger;

        private JsonSerializerOptions _jsonOption = new()
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
        };

        public async Task<HealthResponse?> GetHealthAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/health");

                if (!response.IsSuccessStatusCode)
                {
                    return null;
                }

                var json = await response.Content.ReadAsStringAsync();

                return JsonSerializer.Deserialize<HealthResponse>(json, _jsonOption);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error checking API health");

                return null;
            }
        }

        public async Task<StatsResponse?> GetStatsAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/stats");

                if (!response.IsSuccessStatusCode)
                {
                    return null;
                }

                var json = await response.Content.ReadAsStringAsync();
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true,
                    PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
                };

                return JsonSerializer.Deserialize<StatsResponse>(json, options);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting stats");

                return null;
            }
        }

        public async Task<QueryResponse?> QueryAsync(QueryRequest request)
        {
            try
            {
                var response = await _httpClient.PostAsJsonAsync("/query", request, _jsonOption);

                if (!response.IsSuccessStatusCode)
                {
                    var error = await response.Content.ReadAsStringAsync();

                    _logger.LogError("Query failed: {Error}", error);

                    return null;
                }

                var json = await response.Content.ReadAsStringAsync();

                return JsonSerializer.Deserialize<QueryResponse>(json, _jsonOption);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error querying documents");

                return null;
            }
        }

        public async Task<UploadResponse?> UploadDocumentsAsync(IEnumerable<IBrowserFile> files)
        {
            try
            {
                using var content = new MultipartFormDataContent();

                foreach (var file in files)
                {
                    var fileContent = new StreamContent(file.OpenReadStream(maxAllowedSize: 10 * 1024 * 1024));

                    fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(file.ContentType);
                    content.Add(fileContent, "files", file.Name);
                }

                var response = await _httpClient.PostAsync("/upload", content);

                if (!response.IsSuccessStatusCode)
                {
                    var error = await response.Content.ReadAsStringAsync();

                    _logger.LogError("Upload failed: {Error}", error);

                    return null;
                }

                var json = await response.Content.ReadAsStringAsync();

                return JsonSerializer.Deserialize<UploadResponse>(json, _jsonOption);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error uploading documents");

                return null;
            }
        }
    }
}