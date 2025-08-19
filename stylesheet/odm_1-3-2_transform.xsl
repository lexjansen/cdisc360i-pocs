<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
    version="2.0"
    exclude-result-prefixes="odm">
    <xsl:output method="html" doctype-system="about:legacy-compat" indent="no"/>

    <!-- Display DataType and Length (0/1)? -->
    <xsl:param name="displayDataTypeLength" select="0" />

    <!-- Display DataType and Length (0/1)? -->
    <xsl:param name="displayAnnotations" select="1" />

    <xsl:template match="/">
        <html lang="en">
            <head>
                <title><xsl:value-of select="//odm:FormDef/@Name"/></title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                    h2 { color: #34495e; margin-top: 30px; background: #ecf0f1; padding: 10px; border-left: 4px solid #3498db; }
                    h3 { color: #2980b9; margin-top: 20px; }
                    .form { margin: 20px 0; padding: 15px; border: 1px solid #bdc3c7; border-radius: 5px; background: #fafafa; }
                    .concept-group { margin: 20px 0; padding: 15px; border: 1px solid #bdc3c7; border-radius: 5px; background: #fafafa; }
                    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                    th, td { padding: 8px 12px; text-align: left; border: 1px solid #bdc3c7; }
                    th { background-color: #3498db; color: white; font-weight: bold; }
                    tr:nth-child(even) { background-color: #f8f9fa; }
                    .field-label { font-weight: bold; color: #2c3e50; min-width: 150px; }
                    .field-value { padding: 5px; }
                    input[type="text"], input[type="date"], input[type="number"], select {
                        width: 250px; padding: 5px; border: 1px solid #bdc3c7; border-radius: 3px;
                        font-size: 14px;
                    }
                    input:focus, select:focus { outline: none; border-color: #3498db; box-shadow: 0 0 5px rgba(52, 152, 219, 0.3); }
                    .coding-info { font-weight: bold; font-size: 13px; color: #00aa00; font-style: italic; margin-top: 5px; }
                    .prespecified { background-color: #e8f5e8; font-weight: bold; }
                    .mandatory { color: #e74c3c; }
                    .question { font-weight: bold; color: #2980b9; margin-bottom: 10px; }
                    .annotation {background-color: LightYellow; border: 1px solid #ccc; padding: 5px; }
                    .form-instruction {
                      vertical-align: top;
                      white-space: pre; /* CSS 2.0 */
                      white-space: pre-wrap; /* CSS 2.1 */
                      /* CSS 3.0 */
                      white-space: -pre-wrap; /* Opera 4-6 */
                      white-space: -o-pre-wrap; /* Opera 7 */
                      white-space: -moz-pre-wrap; /* Mozilla */
                      white-space: -hp-pre-wrap; /* HP Printers */
                      word-wrap: break-word; /* IE 5+ */
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Study:<xsl:value-of select="/odm:ODM/odm:Study[1]/odm:GlobalVariables/odm:StudyName"/></h1>
                    <p><strong>Protocol:</strong> <xsl:value-of select="/odm:ODM/odm:Study[1]/odm:GlobalVariables/odm:ProtocolName"/></p>
                    <p><strong>Description:</strong> <xsl:value-of select="/odm:ODM/odm:Study[1]/odm:GlobalVariables/odm:StudyDescription"/></p>
                    <p><strong>Metadata Version:</strong> <xsl:value-of select="/odm:ODM/odm:Study[1]/odm:MetaDataVersion[1]/@Description"/></p>

                    <form id="cdashForm" method="post">
                        <xsl:apply-templates select="//odm:FormDef"/>
                    </form>
                </div>
            </body>
        </html>
    </xsl:template>

    <xsl:template match="odm:FormDef">
        <div class="form-section">
            <h2><xsl:value-of select="@Name"/></h2>
            <!-- <p><xsl:value-of select="odm:Description/odm:TranslatedText"/></p> -->
            <xsl:if test="$displayAnnotations = 1">
              <xsl:if test="odm:Alias[@Context='formAnnotation']">
                  <div class='annotation'><xsl:value-of select="odm:Alias[@Context='formAnnotation']/@Name"/></div>
              </xsl:if>
            </xsl:if>

            <xsl:for-each select="odm:ItemGroupRef">
                <xsl:variable name="groupOID" select="@ItemGroupOID"/>
                <xsl:apply-templates select="//odm:ItemGroupDef[@OID=$groupOID]"/>
            </xsl:for-each>
        </div>
    </xsl:template>

    <xsl:template match="odm:ItemGroupDef">
        <div class="concept-group">

            <h3>
                <xsl:value-of select="@Name"/>
            </h3>
            <!-- <p><xsl:value-of select="odm:Description/odm:TranslatedText"/></p> -->

            <xsl:if test="$displayAnnotations = 1">
                <xsl:if test="odm:Alias[@Context='formSectionAnnotation']">
                    <div class='annotation'>
                        <xsl:value-of select="odm:Alias[@Context='formSectionAnnotation']/@Name"/>
                    </div>
                </xsl:if>
            </xsl:if>
            <xsl:if test="odm:Alias[@Context='formSectionCompletionInstruction']">
                <div class='form-instruction'>
                    <xsl:value-of select="odm:Alias[@Context='formSectionCompletionInstruction']/@Name"/>
                </div>
            </xsl:if>

            <xsl:if test="$displayAnnotations = 1">

                <xsl:for-each select="odm:Coding">
                      <div class="coding-info">
                          <xsl:value-of select="@SystemName"/>: <xsl:value-of select="@Code"/> (<xsl:value-of select="@System"/>)
                      </div>
                </xsl:for-each>
            </xsl:if>

            <table>
                <thead>
                    <tr>
                        <th>Field</th>
                        <th>Value</th>
                        <xsl:if test="$displayAnnotations = 1">
                          <th>Details</th>
                        </xsl:if>

                    </tr>
                </thead>
                <tbody>
                    <xsl:for-each select="odm:ItemRef">
                        <xsl:sort select="@OrderNumber" data-type="number"/>
                        <xsl:variable name="itemOID" select="@ItemOID"/>
                        <xsl:variable name="itemDef" select="//odm:ItemDef[@OID=$itemOID]"/>

                        <tr>
                            <td class="field-label">
                                <xsl:choose>
                                    <xsl:when test="$itemDef/odm:Alias[@Context='prompt']">
                                        <xsl:value-of select="$itemDef/odm:Alias[@Context='prompt']/@Name"/>
                                    </xsl:when>
                                    <xsl:when test="$itemDef/odm:Question">
                                        <xsl:value-of select="$itemDef/odm:Question/odm:TranslatedText"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="$itemDef/@Name"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                                <xsl:if test="@Mandatory='Yes'">
                                    <span class="mandatory"> *</span>
                                </xsl:if>
                            </td>
                            <td class="field-value">
                                <xsl:choose>
                                    <!-- Pre-specified values (read-only) -->
                                    <xsl:when test="@PreSpecifiedValue">
                                        <input type="text" name="{$itemDef/@Name}" value="{@PreSpecifiedValue}"
                                               class="prespecified" readonly="readonly"/>
                                    </xsl:when>

                                    <!-- Date fields -->
                                    <xsl:when test="$itemDef/@DataType='date'">
                                        <input type="date" name="{$itemDef/@Name}" />
                                    </xsl:when>

                                    <!-- Numeric fields (ORRES) -->
                                    <xsl:when test="$itemDef/@DataType='integer'">
                                        <input type="number" name="{$itemDef/@Name}"
                                               />
                                    </xsl:when>

                                    <!-- Dropdown for coded values -->
                                    <xsl:when test="$itemDef/odm:CodeListRef">
                                        <xsl:variable name="codeListOID" select="$itemDef/odm:CodeListRef/@CodeListOID"/>
                                        <xsl:variable name="codeList" select="//odm:CodeList[@OID=$codeListOID]"/>

                                        <select name="{$itemDef/@Name}">
                                            <option value="">-- Select --</option>
                                            <xsl:for-each select="$codeList/odm:CodeListItem">
                                                <option value="{@CodedValue}">
                                                    <xsl:choose>
                                                        <xsl:when test="odm:Decode/odm:TranslatedText">
                                                            <xsl:value-of select="odm:Decode/odm:TranslatedText"/>
                                                        </xsl:when>
                                                        <xsl:otherwise>
                                                            <xsl:value-of select="@CodedValue"/>
                                                        </xsl:otherwise>
                                                    </xsl:choose>
                                                </option>
                                            </xsl:for-each>
                                            <xsl:for-each select="$codeList/odm:EnumeratedItem">
                                                <option value="{@CodedValue}">
                                                    <xsl:value-of select="@CodedValue"/>
                                                </option>
                                            </xsl:for-each>
                                        </select>
                                    </xsl:when>

                                    <!-- Default text input -->
                                    <xsl:otherwise>
                                        <input type="text" name="{$itemDef/@Name}"
                                               maxlength="{$itemDef/@Length}"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </td>

                            <xsl:if test="$displayAnnotations = 1">
                              <td>
                                  <xsl:if test="$displayDataTypeLength = 1">
                                      <div>
                                          <strong>Type:</strong> <xsl:value-of select="$itemDef/@DataType"/>
                                          <xsl:if test="$itemDef/@Length">
                                              (<xsl:value-of select="$itemDef/@Length"/>)
                                          </xsl:if>
                                      </div>
                                  </xsl:if>


                                  <xsl:if test="$itemDef/odm:Alias[@Context='SDTM']">
                                      <div class='annotation'><xsl:value-of select="$itemDef/odm:Alias[@Context='SDTM']/@Name"/></div>
                                  </xsl:if>

                                  <xsl:if test="$itemDef/odm:CodeListRef">
                                      <xsl:variable name="codeListOID" select="$itemDef/odm:CodeListRef/@CodeListOID"/>
                                      <xsl:variable name="codeList" select="//odm:CodeList[@OID=$codeListOID]"/>
                                      <div class="coding-info">
                                          <strong>CodeList: </strong> <xsl:value-of select="$codeList/@Name"/>
                                          <xsl:if test="$codeList/odm:Coding">
                                              (<xsl:value-of select="$codeList/odm:Coding/@Code"/>)
                                          </xsl:if>
                                      </div>
                                  </xsl:if>
                              </td>
                            </xsl:if>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>