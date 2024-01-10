# Message Parsing Assistant

#### Description
**This software supports DLT/645-2007 and Southern Grid 2003 protocol parsing, enabling the parsing of messages based on data flag contents. It does not have fixed predefined data identifiers but allows for extension and customization of message parsing rules.**

#### Software Architecture
Python 3.11

#### Installation Guide
1. Install dependencies using the following command:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the program:
   ```bash
   python Assistant.py
   ```

#### Usage Instructions
- The configuration file for DLT/645-2007 parsing is `app/config/DLT645.xml`.
- The configuration file for the Southern Grid 2003 protocol is `app/config/CSG13.xml`.

#### Configuration File Definition
##### Parent Elements
- `<dataItem>`:
  - **Attributes:**
    - `id`: A unique identifier for the data item used to distinguish it within the configuration file.
    - `protocol`: Specifies the communication protocol being used.
    - `region`: Indicates the province where the data item belongs.

  - **Example**
      ```xml
      <dataItem id="E1800023" protocol="csg13" region="南网">
        <name>拓扑关系详细信息</name>
        <length>unknown</length>
        <splitByLength>
          <name>总记录条数</name>
          <length>1</length>
          <type>BIN</type>
        </splitByLength>
        <splitByLength>
          <name>本帧记录数</name>
          <length>1</length>
          <type>BIN</type>
        </splitByLength>
        <splitByLength>
          <name>起始记录序号</name>
          <length>1</length>
          <type>BIN</type>
        </splitByLength>
        <splitByLength>
          <name>节点信息</name>
          <length>unknown</length>
          <type>TOPONODEINFO</type>
        </splitByLength>
      </dataItem>
      ```

  - **Notes**
    - For block data, all sub-items must be defined in the configuration file alongside the main data identifier; incremental sub-items are not supported. Each sub-item's definition should be included.
      ```xml
      <dataItem id="数据标识" protocol="规约类型" region="省份">
        <name>(当前)组合有功电能数据块</name>
        <length>256</length>
        <dataItem id="00000000">
          <name>(当前)组合有功总电能</name>
          <length>4</length>
          <unit>kWh</unit>
          <decimal>2</decimal>
        </dataItem>
        <dataItem id="00000100">
          <name>(当前)组合有功费率1电能</name>
          <length>4</length>
          <unit>kWh</unit>
          <decimal>2</decimal>
        </dataItem>
        <dataItem id="00000200">
          <name>(当前)组合有功费率2电能</name>
          <length>4</length>
          <unit>kWh</unit>
          <decimal>2</decimal>
        </dataItem>
      </dataItem>
      ```

- `<template>`:
  - **Attributes:**
    - `id`: A unique identifier for the template type, used to differentiate it in the configuration file.
    - `protocol`: Specifies the communication protocol being used.
    - `region`: Indicates the province where the template applies.

  - **Example**
    ```xml
    <template id="ARD1" protocol="csg13" region="南网">
      <splitByLength>
        <name>告警状态</name>
        <length>1</length>
        <value key="00">恢复</value>
        <value key="01">发生</value>
      </splitByLength>
      <splitByLength>
        <name>告警发生时间</name>
        <length>6</length>
        <time>ssmmhhDDMMYY</time>
      </splitByLength>
    </template>
    ```

##### Common Sub-elements
- `<name>`: Describes the name of the entire data item.
- `<length>`: Specifies the length of the data item. When a data item is variable-length, set this field to `unknown` and use `<lengthrule>`.
- `<unit>`: The unit for the data item.
- `<decimal>`: Specifies the number of decimal places for the data item (not required if no decimal places exist).
- `<sign>`: Indicates whether the data can be signed (yes/no), not needed if the data is unsigned.
- `<type>`: Specifies the data type of the item, with built-in support for `BIN`, `BCD`, `ASCII`, `PN`, `IPWITHPORT`, `FRAME645`, `ITEM`, `CSG13`. `PN` represents measurement points, `IPWITHPORT` indicates an IP address + port, `FRAME645` refers to a 645 protocol message, `ITEM` denotes a custom data item, and `CSG13` pertains to the Southern Grid 13 protocol message. Other types require customization and work with `<template>`.
- `<splitByLength>`: Denotes that the data item content should be split by length.
  - **Mandatory Sub-elements**
    - `<name>`: Describes the data item's name.
    - `<length>`: Specifies the length of the data item.
- `<time>`: Represents the time format for data, supporting `CC`-Century, `YY`-Year, `MM`-Month, `DD`-Day, `HH`-Hour, `mm`-Minute, `ss`-Second, combined in the order they appear in the message.
- `<lengthrule>`: Specifies the length rule for the data item when it's variable-length, e.g., `<lengthrule>7 * Number of Responded Power Distribution Nodes</lengthrule>`
  ```xml
  <splitByLength>
      <name>应答的台区节点总数量</name>
      <length>2</length>
      <type>BCD</type>
  </splitByLength>
  <splitByLength>
      <name>台区识别结果</name>
      <length>unknown</length>
      <lengthrule>7 * 应答的台区节点总数量</lengthrule>
      <type>IDENTIFICATION_RESULTS</type>
  </splitByLength>
  ```
- `<value>`: Provides the meaning of the content, e.g., `<value key="00">Recovered</value>`
- `<splitbit>`: Indicates that each bit within a byte needs to be split, defining the meaning of each bit.
  ```xml
	<dataItem id="04000503">
		<name>运行状态字3</name>
		<length>2</length>
		<splitbit>
			<bit id="0">
				<name>当前运行时段</name>
				<value key="1">第二套</value>
				<value key="0">第一套</value>
			</bit>
			<bit id="1-2">
				<name>供电方式</name>
				<value key="00">主电源</value>
				<value key="01">辅助电源</value>
				<value key="10">电池供电</value>
			</bit>
			<bit id="3">
				<name>编程允许</name>
				<value key="1">许可</value>
				<value key="0">禁止</value>
			</bit>
			<bit id="4">
				<name>继电器状态</name>
				<value key="1">断</value>
				<value key="0">通</value>
			</bit>
			<bit id="5-15">
				<name>保留</name>
			</bit>
		</splitbit>
	</dataItem>
  ```
  - **Mandatory Sub-elements**
    - `<name>`: Describes the data item's name.
    - `<length>`: Specifies the length of the data item.
    - `<bit>`: Defines the meaning of each split bit, supporting bit ranges denoted by `-`, e.g., `1-2`.