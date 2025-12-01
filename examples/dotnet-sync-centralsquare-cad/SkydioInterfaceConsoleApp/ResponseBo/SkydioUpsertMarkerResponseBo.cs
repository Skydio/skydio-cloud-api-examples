using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SkydioInterfaceConsoleApp.ResponseBo
{

    internal class SkydioUpsertMarkerResponseBo
    {
        public SkydioResponseDataBo data {  get; set; }
        public SkydioResponseMetaBo meta { get; set; }
        public int skydio_error_code { get; set; }
        public int status_code { get; set; }
    }

    internal class SkydioResponseDataBo
    {
        public SkydioResponseMarkerBo marker { get; set; }
    }
    
    internal class SkydioResponseMarkerBo
    {
        public string area { get; set; }
        public string description { get; set; }
        public string event_time { get; set; }
        public decimal latitude { get; set; }
        public decimal longitude { get; set; }
        public string source_name { get; set; }
        public string title { get; set; }
        public string type { get; set; }
        public string uuid { get; set; }
        public SkydioResponseDataIncidentDetailsBo marker_details { get; set; }

    }

    internal class SkydioResponseDataIncidentDetailsBo
    {
        public string code { get; set; }
        public string incident_id { get; set; }
        public string priority { get; set; }
    }

    

    internal class SkydioResponseMetaBo
    {
        public decimal time { get; set; }
    }
}
