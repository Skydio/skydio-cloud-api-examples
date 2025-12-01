using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SkydioInterfaceConsoleApp.Models.DB.CAD_Manual;

[Table("incident")]
public partial class Incident
{
    [Key]
    public int callrefno { get; set; }
    public DateTime? calltime { get; set; }
    public string inci_id { get; set; } 
    public string priority { get; set; }
    public string service { get; set; }
    public string agency { get; set; }
    public string business { get; set; }
    public string callernm { get; set; }
    public string latitude { get; set; }
    public string longitude { get; set; }
    public string naturecode { get; set; }
    public string nature { get; set; }
    public string statbeat { get; set; }

}
