<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
				xmlns:NS="http://www.newworldsystems.com/Aegis/CAD/Peripheral/CallExport/2011/02"
				version="1.0">
	<xsl:output method="text"
				indent="no" />

	<!-- Hide everything -->
	<xsl:template match="text() | @*" />

	<!-- Template for Root Call node to be included. This also determines the order it displays in the output. -->
	<xsl:template match="/NS:Call">	
		<xsl:copy>{
	"marker_details":{<xsl:apply-templates select="NS:CallSource"/>  
		"incident_id": "<xsl:value-of select="$ORIsIncidentNumber"/>",
		"priority":"<xsl:copy-of select="NS:AgencyContexts/NS:AgencyContext[NS:AgencyType='Police']/NS:Priority"/>"
		},<xsl:apply-templates select="NS:Incidents"/>
<xsl:apply-templates select="NS:Location/NS:PoliceBeat"/>			
			<xsl:apply-templates select="NS:NatureOfCall"/>
		<xsl:choose>			
			 <!--true if any nil-like attribute exists with value 'true'--> 
			<xsl:when test="normalize-space(NS:NatureOfCall)=''">
				<xsl:text>
	"description": "Undescribed",</xsl:text>
			</xsl:when>			
			<xsl:otherwise>
	"description": "<xsl:call-template name="format-quotes">
            <xsl:with-param name="text" select="NS:NatureOfCall"/>
          </xsl:call-template>",</xsl:otherwise>			
		</xsl:choose>
<!--<xsl:apply-templates select="NS:NatureOfCall"/>-->
<xsl:apply-templates select="NS:CreateDateTime"/>
<xsl:apply-templates select="NS:CallId"/>
<xsl:apply-templates select="NS:Location/NS:LatitudeY"/>
<xsl:apply-templates select="NS:Location/NS:LongitudeX"/>
<xsl:apply-templates select="NS:CallNumber"/>
<xsl:apply-templates select="NS:AgencyContexts"/>
}</xsl:copy>
	</xsl:template>

	<!-- Recursive format template this replaces " with ' -->
	<xsl:template name="format-quotes">
		<xsl:param name="text"/>
		<xsl:choose>
			<xsl:when test="contains($text, '&quot;')">
				<xsl:value-of select="substring-before($text, '&quot;')"/>
				<xsl:text>'</xsl:text>
				<xsl:call-template name="format-quotes">
					<xsl:with-param name="text" select="substring-after($text, '&quot;')"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$text"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
		
	<!-- code -->
	<xsl:template match="/NS:Call/NS:CallSource">
		"code": "<xsl:copy-of select="."/>",</xsl:template>	
	
	<!-- incident_id -->
	<xsl:variable name="ORIsIncidentNumber">
	<xsl:value-of select="/NS:Call/NS:Incidents/NS:Incident[NS:Jurisdiction='{Your ORI Here}']/NS:Number"/>			
	</xsl:variable>
	
	<!--area-->
	<xsl:template match="/NS:Call/NS:Location/NS:PoliceBeat">   
	"type": "INCIDENT",
	"area": "<xsl:copy-of select="."/>",</xsl:template>	
	
	<!-- event_time -->
	<xsl:variable name="dt" select="/NS:Call/NS:CreateDateTime"/>
		<xsl:template match="/NS:Call/NS:CreateDateTime">
	"event_time": "<xsl:copy-of select="."/>",</xsl:template>
	
	<!--call_id-->
	<xsl:template match="/NS:Call/NS:CallId">
	"call_id": "<xsl:copy-of select="."/>",</xsl:template>	
	
	<!-- latitude -->
	<xsl:template match="/NS:Call/NS:Location/NS:LatitudeY">
	<xsl:choose>
		<xsl:when test="normalize-space(.) = ''">			
			<!-- Output when LatitudeY is empty -->
			<xsl:text></xsl:text>
		</xsl:when>
			<!-- Output when LatitudeY has content -->
		<xsl:otherwise>
	"latitude": <xsl:copy-of select="."/>,</xsl:otherwise>
	</xsl:choose>
	</xsl:template>
	
	<!-- longitude -->
	<xsl:template match="/NS:Call/NS:Location/NS:LongitudeX">
	<xsl:choose>
		<xsl:when test="normalize-space(.) = ''">			
			<!-- Output when LongitudeX is empty -->
			<xsl:text></xsl:text>
		</xsl:when>
			<!-- Output when LongitudeX has content -->
		<xsl:otherwise>
	"longitude": <xsl:copy-of select="."/>,</xsl:otherwise>
	</xsl:choose>
	</xsl:template>

	<!--source_name/title-->
	<xsl:template match="/NS:Call/NS:AgencyContexts">
		<xsl:copy>
	"source_name": "YOUR_SOURCE_NAME_HERE",
	"title": "<xsl:copy-of select="/NS:Call/NS:CallNumber"/>: <xsl:apply-templates select="NS:AgencyContext"/>"</xsl:copy>
	</xsl:template>

	<xsl:template match="NS:AgencyContext[NS:AgencyType='Police']">
		<xsl:copy>
			<xsl:copy-of select="NS:CallType"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>