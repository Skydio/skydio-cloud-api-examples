using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SkydioInterfaceConsoleApp.ResponseBo
{

    internal class SkydioGetMarkersResponseBo
    {
        public SkydioGetMarkersResponseDataBo data {  get; set; }
        public SkydioResponseMetaBo meta { get; set; }
        public int skydio_error_code { get; set; }
        public int status_code { get; set; }
    }

    internal class SkydioGetMarkersResponseDataBo
    {
        public List<SkydioResponseMarkerBo> markers { get; set; }
        public SkydioResponsePaginationBo pagination { get; set; }
    }

    internal class SkydioResponsePaginationBo
    {
        public int current_page { get; set; }
        public int max_per_page { get; set; }
        public int total_pages { get; set; }
    }
}
