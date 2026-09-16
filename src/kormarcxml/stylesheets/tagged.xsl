<?xml version="1.0" encoding="UTF-8"?>
<!-- Original KORMARCXML implementation, MIT; display-only, no semantic crosswalk. -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:m="http://www.loc.gov/MARC21/slim" exclude-result-prefixes="m">
  <xsl:output method="text" encoding="UTF-8"/>
  <xsl:template match="/"><xsl:apply-templates select="m:record | m:collection/m:record"/></xsl:template>
  <xsl:template match="m:record"><xsl:apply-templates select="*"/></xsl:template>
  <xsl:template match="m:leader"><xsl:text>=LDR  </xsl:text><xsl:value-of select="."/><xsl:text>&#10;</xsl:text></xsl:template>
  <xsl:template match="m:controlfield"><xsl:text>=</xsl:text><xsl:value-of select="@tag"/><xsl:text>  </xsl:text><xsl:value-of select="."/><xsl:text>&#10;</xsl:text></xsl:template>
  <xsl:template match="m:datafield"><xsl:text>=</xsl:text><xsl:value-of select="@tag"/><xsl:text>  </xsl:text><xsl:value-of select="translate(@ind1,' ','#')"/><xsl:value-of select="translate(@ind2,' ','#')"/><xsl:apply-templates select="m:subfield"/><xsl:text>&#10;</xsl:text></xsl:template>
  <xsl:template match="m:subfield"><xsl:text>$</xsl:text><xsl:value-of select="@code"/><xsl:value-of select="."/></xsl:template>
</xsl:stylesheet>
