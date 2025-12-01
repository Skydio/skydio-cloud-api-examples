using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace SkydioInterfaceConsoleApp.Models.DB.CAD_Manual;

public partial class CadContext : DbContext
{
    private readonly IConfiguration config;
    public CadContext(IConfiguration config)
    {
        this.config = config;
    }

    public CadContext(DbContextOptions<CadContext> options)
        : base(options)
    {
    }


    public virtual DbSet<Incident> Incident { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        optionsBuilder.UseSqlServer(config.GetConnectionString("CADRPT"));
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Incident>();

    }

    partial void OnModelCreatingPartial(ModelBuilder modelBuilder);
}
