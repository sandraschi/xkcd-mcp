# Per-repo fleet start config for xkcd-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'xkcd-mcp'
    BackendPort  = 10778
    FrontendPort = 10779
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'xkcd_mcp.app:app'
        SyncExtras    = @('dev')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '10778' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
