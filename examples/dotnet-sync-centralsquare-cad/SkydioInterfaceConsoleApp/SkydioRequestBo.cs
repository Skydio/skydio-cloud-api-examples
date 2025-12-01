using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SkydioInterfaceConsoleApp
{
    internal class SkydioUpdateMarkerRequestBo
    {
        public string area { get; set; }
        public string description { get; set; }
        public string event_time { get; set; }
        public decimal latitude { get; set; }
        public decimal longitude { get; set; }
        public string source_name { get; set; } = "OS CAD";
        public string title { get; set; }
        public string type { get; set; } = "INCIDENT";
        public string? uuid { get; set; }
        public SkydioUpdateMarkerRequestIncidentDetailsBo marker_details { get; set; } = new SkydioUpdateMarkerRequestIncidentDetailsBo();

    }

    internal class SkydioCreateMarkerRequestBo
    {
        public string area { get; set; }
        public string description { get; set; }
        public string event_time { get; set; }
        public decimal latitude { get; set; }
        public decimal longitude { get; set; }
        public string source_name { get; set; } = "OS CAD";
        public string title { get; set; }
        public string type { get; set; } = "INCIDENT";
        public SkydioUpdateMarkerRequestIncidentDetailsBo marker_details { get; set; } = new SkydioUpdateMarkerRequestIncidentDetailsBo();

    }

    internal class SkydioUpdateMarkerRequestIncidentDetailsBo
    {
        public string code { get; set; }
        public string incident_id { get; set; }
        public string priority { get; set; }
    }
}
