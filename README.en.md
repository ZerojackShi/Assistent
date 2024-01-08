# 报文解析助手

#### 描述
**该软件支持DLT/645-2007、南网2003规约解析，能根据数据标志内容定义解析报文，非内置固定数据标识，可自行扩展，支持自定义报文解析**

#### 软件架构
Python 3.11

#### 安装教程
* 使用下列命令安装依赖
```bash
pip install -r requirements.txt
```
* 运行程序
```bash
python Assistant.py
```

#### 使用说明
* DLT/645-2007解析配置文件为`app/config/DLT645.xml`
* 南网2003规约解析配置文件为`app/config/CSG13.xml`
* 配置文件定义如下：

##### `<dataItem>`:
- **属性:**
  - `id`: 数据项的唯一标识符，用于在配置文件中区分不同的数据项。
  - `protocol`: 指定使用的通信协议。
  - `region`: 表示数据项所属的省份。

- **子元素:**
  - `<name>`: 描述整个数据项的名称。
  - `<length>`: 指定数据项的长度，当数据项为变长时，该字段填写`unknown`,并配合`<lengthrule>`使用。
  - `<unit>`: 数据项单位。
  - `<decimal>`: 数据项的小数位，没有小数位时可以不增加该字段。
  - `<sign>`: 指定数据可以具有符号（正(yes)/负(no)），无符号时可以不增加该字段。
  - `<type>`: 指定数据项的数据类型，内置支持`BIN`,`BCD`,`ASCII`,`PN`,`IPWITHPORT`,`FRAME645`,`ITEM`,`CSG13`。其中`PN`代表测量点，`IPWITHPORT`代表IP地址+端口，`FRAME645`代表645协议报文，`ITEM`代表自定义数据项，`CSG13`代表南网13协议报文。其他模板类型需要自定义，并配合`<template>`使用
  - `<template>`: 指定数据项的模板，当数据项为自定义数据项时，需要添加该字段，如：`<template id="ARD1" protocol="csg13" region="南网">`
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
        <time>YYMMDDhhmmss</time>
      </splitByLength>
    </template>
    ```
  - `<splitByLength>`: 表示数据项内容按照长度拆分。
    - **必含子元素**
      - `<name>`: 描述数据项的名称。
      - `<length>`: 指定数据项的长度。
  - `<time>` :表示数据的时间格式，支持`CC`-世纪,`YY`-年,`MM`-月,`DD`-日,`HH`-时,`mm`-分,`ss`-秒，组合使用。
  - `<lengthrule>`: 指定数据项的长度规则，当数据项为变长时，填写长度计算规则，如：`<lengthrule>7 * 应答的台区节点总数量</lengthrule>`

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
含有块数据的需要将块数据的数据标识与分项数据一起定义，分项数据不支持自增，有多少个分项数据就需要将所有分项数据均定义到配置文件中；