# XSLT Convert CAD Call to Marker Example

This example demonstrates how to transform a CAD event XML file to a Skydio marker XML file using XSLT.

We provide two options to run the XSLT transform, using `xsltproc` or `Saxon` in Java.

- The transform is in `convert_cad_call_to_marker.xslt`
- The sample input is in `sample_input_cad_call.xml`
- The sample output is in `sample_output_marker.xml`

## Option 1, using xsltproc

### Setup

Ubuntu/Debian/Windows WSL:

```bash
sudo apt-get install xsltproc
```

MacOS (Homebrew):

```bash
brew install libxslt
```

### Run

Run xsltproc, taking `sample_input_cad_call.xml` as input and writing to `sample_output_marker.xml` as output:

```bash
xsltproc \
  --output sample_output_marker.xml \
  convert_cad_call_to_marker.xslt \
  sample_input_cad_call.xml
```

## Option 2, using Saxon

### Setup

Download Saxon HE as a zip from their official Github: https://github.com/Saxonica/Saxon-HE/tree/main/12/Java

Example, here we will use: `SaxonHE12-9J.zip`

Unzip the zip file in this current folder:

```bash
unzip SaxonHE12-9J.zip
```

### Run

Run Saxon, taking `sample_input_cad_call.xml` as input and writing to `sample_output_marker.xml` as output:

```bash
java -cp "SaxonHE12-9J/saxon-he-12.9.jar:SaxonHE12-9J/lib/xmlresolver-5.3.3.jar:SaxonHE12-9J/lib/xmlresolver-5.3.3-data.jar" \
  net.sf.saxon.Transform \
  -s:sample_input_cad_call.xml \
  -xsl:convert_cad_call_to_marker.xslt \
  -o:sample_output_marker.xml
```
