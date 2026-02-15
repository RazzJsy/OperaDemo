using OperaDemoWeb.Components;
using OperaDemoWeb.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents().AddInteractiveServerComponents();

builder.Services.AddHttpClient<ApiService>(client =>
{
    var backendUrl = builder.Configuration.GetValue<string>("BackendApiUrl") ?? "http://localhost:8000";

    client.BaseAddress = new Uri(backendUrl);
});

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
}

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>().AddInteractiveServerRenderMode();

app.Run();
