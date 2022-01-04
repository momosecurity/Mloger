<template>
  <div class="layout">
    <Row style="padding: 0 5px">
      <iCol span="12">
        <Row style="margin: 0 5px">
          <Button @click="searchGo()" type="primary" size="small" class="search-btn" style="width: 65px">GO
          </Button>
          <Button
              @click="requestContentFormat('json')"
              type="primary"
              class="search-btn"
              size="small"
              style="width: 65px;margin-left: 5px"
          >ToJson
          </Button>
          <Button
              @click="requestContentFormat('raw')"
              type="primary"
              class="search-btn"
              size="small"
              style="width: 65px;margin-left: 5px"
          >ToRaw
          </Button>
          <Button
              type="primary"
              class="search-btn"
              size="small"
              style="width: 65px;margin-left: 5px"
              @click="addFlag"
          >&nbsp;&nbsp;add §
          </Button>
          <Button
              type="primary"
              class="search-btn"
              size="small"
              style="width: 65px;margin-left: 5px"
              @click="clearFlag"
          >&nbsp;&nbsp;clear §
          </Button>
        </Row>
        <Row style="margin: 5px 5px;">
          <div style="padding: 2px">
            并发数:
          </div>
          <Input
              placeholder="并发数"
              v-model="query.concurrent_num"
              type="number"
              size="small"
              :style="{ width: '60px' }"
          />
          <Select v-model="query.type" :style="{ width: '120px', 'margin-left': '10px' }" size="small">
            <Option v-for="item of encodeTypeList" :key="item" :value="item">{{
                item
              }}
            </Option>
          </Select>
          <Button type="primary" :style="{ 'margin-left': '10px' }" size="small" @click="showPayload"
          >payload设置
          </Button
          >
        </Row>
        <Row>
          <Card :bordered="true" style="width: 100%">
            <p slot="title">Request</p>
            <Input
                ref="requestEl"
                type="textarea"
                v-model="request"
                :autosize="{ minRows: 21, maxRows: 21 }"
                @select.native="bodyRequestSelectEvent"
            />
          </Card>
        </Row>
      </iCol>
      <iCol span="12">
        <Row style="margin: 0 5px">
          <Button @mouseenter.native="modalHistory = true" size="small"
                  style="width: 80px; background:#FF8F0B;color:#FFFFFF;">历史记录
          </Button>
        </Row>
        <Row style="margin: 5px 5px">
          <Checkbox
              v-model="query.keepua"
              size="small"
              border
              :style="{ 'border-color': 'rgba(243, 246, 249, 0.2)' }"
          >保留ua
          </Checkbox
          >
          <Checkbox
              v-model="query.ishttps"
              size="small"
              border
              :style="{ 'border-color': 'rgba(243, 246, 249, 0.2)' }"
          >HTTPS
          </Checkbox
          >
        </Row>
        <Row>
          <Card :bordered="true" style="width: 100%">
            <p slot="title">Response</p>
            <Input
                ref="responseEl"
                type="textarea"
                v-model="response"
                readonly
                :autosize="{ minRows: 21, maxRows: 21 }"
                @select.native="bodyResponseSelectEvent"
            />
          </Card>
        </Row>
      </iCol>
    </Row>
    <Row v-if="selectDataList.length>0" style="padding: 10px 10px;width:100%;">
      <Collapse v-model="resultCollapse" style="width:100%;">
        <Panel v-for="item in selectDataList" :key="item">
          <span>
            {{ item.title }}   <Button size="small" @click="openNewUrl(item.url)"
                                       style="width: 60px;margin-right: 50px;float: right;margin-top: 7px"
                                       type="primary">重放</Button>
          </span>
          <div slot="content">
            <Row>
              <iCol span="12" :style="{ 'padding-right': '20px' }">
                <Card :bordered="true">
                  <div slot="title">Request</div>
                  <Input
                      type="textarea"
                      readonly
                      v-model="item.request"
                      :autosize="{ minRows: 21, maxRows: 21 }"
                  />
                </Card>
              </iCol>
              <iCol span="12">
                <Card :bordered="true">
                  <div slot="title">Response</div>
                  <Input type="textarea"
                         v-model="item.response"
                         readonly
                         :autosize="{ minRows: 21, maxRows: 21 }"
                  />
                </Card>
              </iCol>
            </Row>
          </div>
        </Panel>
      </Collapse>
    </Row>
    <div id="concurrent_num-id">
      <Modal v-model="concurrentModal.show" :mask-closable="false" :footer-hide="true" :width="650">
        <div slot="header">并发次数: {{ query.concurrent_num }}</div>
        <Row style="display: block">
          <Table highlight-row :columns="concurrentModal.table.headers" :data="concurrentModal.table.body">
            <template slot-scope="{ row, index }" slot="content">
              <span v-if="index===0">{{ row.content }}</span>
              <div v-else v-html="getDifferHtml(concurrentModal.table.body[0].content,row.content)"></div>
            </template>
          </Table>
        </Row>
      </Modal>
    </div>
    <div id="repeater_test">
      <Modal v-model="repeaterTestModal.show" width="1200px" :title="repeaterTestModal.title">
        <Row gutter="2" type="flex" justify="center">
          <Col span="7">
            <Card :bordered="true">
              <p slot="title">Request</p>
              <div ref="repeaterTestModal">
                <Input
                    type="textarea"
                    v-model="request"
                    readonly
                    :autosize="{ minRows: 27, maxRows: 27 }"
                />
              </div>
            </Card>
          </Col>
          <Row v-if="repeaterTestModal.simpleModel">
            <Col span="12">
              <Card :bordered="true" style="width: 400px">
                <p slot="title">变量列表</p>
                <Input
                    type="textarea"
                    v-model="repeaterTestModal.vars"
                    readonly
                    :autosize="{ minRows: 27, maxRows: 27 }"
                />
              </Card>
            </Col>
            <Col span="12">
              <Card :bordered="true" style="width: 400px">
                <p slot="title">
                  <Tooltip max-width="200">
                    变量值列表
                    <Icon type="ios-help" size="20"/>
                <div slot="content">
                  支持范围关键字(range:)枚举和简单js函数枚举
                  范围关键字range:startIndex,endIndex,step, 默认step为1, 例如: range:1,5 ->
                  [1,2,3,4]
                </div>
                </Tooltip>
                </p>
                <Input
                    type="textarea"
                    v-model="repeaterTestModal.dest"
                    :autosize="{ minRows: 27, maxRows: 27 }"
                    :disabled="repeaterTestModal.preShow"
                    :readonly="repeaterTestModal.preShow"
                />
              </Card>
            </Col>
          </Row>
          <div v-else>
            <Col span="14">
              <Card :bordered="true" style="width: 800px">
                <p slot="title">
                  <Tooltip max-width="200">
                    变量列表
                    <Icon type="ios-help" size="20"/>
                <div slot="content">
                  支持范围关键字(range:)枚举和简单js函数枚举
                  范围关键字range:startIndex,endIndex,step, 默认step为1, 例如: range:1,5 ->
                  [1,2,3,4]
                </div>
                </Tooltip>
                </p>
                <div :style="{ height: repeaterTestModal.rawDivHeight }">
                  <Row
                      v-for="item of repeaterTestModal.rawVars"
                      :key="item"
                      :gutter="10"
                      style="padding-top: 10px"
                  >
                    <iCol span="8">
                      <Tag size="large">{{ item }}</Tag>
                    </iCol>
                    <iCol span="16">
                      <Input
                          type="textarea"
                          v-model="repeaterTestModal.rawDest[item]"
                          :placeholder="`参数${item}值内容`"
                          :disabled="repeaterTestModal.preShow"
                          :readonly="repeaterTestModal.preShow"
                      />
                    </iCol>
                  </Row>
                </div>
              </Card>
            </Col>
          </div>
        </Row>
        <div slot="footer">
          <Button
              @click="
                            () => {
                                repeaterTestModal = {
                                    show: false,
                                    vars: '',
                                    dest: '',
                                    rawDest: {},
                                    rawVars: [],
                                    rawDivHeight: '100px',
                                    title: 'Payload配置',
                                    preShow: false,
                                    preRaw: '',
                                };
                            }
                        "
          >取消
          </Button
          >
          <Button type="info" @click="preShowPlayload" v-if="!repeaterTestModal.preShow">预览</Button>
          <Button type="info" @click="preShowPlayload('cancel')" v-else>取消预览</Button>
          <Button
              type="primary"
              @click="
                            () => {
                                setPlayload();
                                repeaterTestModal.show = false;
                                let vars = [];
                                if (repeaterTestModal.simpleModel) {
                                    vars = repeaterTestModal.vars.split('\n');
                                } else {
                                    vars = repeaterTestModal.rawVars;
                                }
                                if (query.type === 'sniper')
                                    query.concurrent_num = query.payload[0].length * vars.length;
                                if (query.type === 'battering ram') query.concurrent_num = query.payload[0].length;
                                if (query.type === 'pitchfork') query.concurrent_num = query.payload[0].length;
                                if (query.type === 'cluster bomb') {
                                    let cn = 1;
                                    for (let idx = 0; idx < query.payload.length; idx++) {
                                        let item = query.payload[idx];
                                        cn *= item.length;
                                    }
                                    query.concurrent_num = cn;
                                }
                            }
                        "
          >确定
          </Button
          >
        </div>
      </Modal>
    </div>
    <Modal v-model="modalHistory" draggable scrollable :mask="false" title="历史记录" width="600"
           ok-text="关闭" cancel-text="">
      <div>
        <Row>
          <iCol>
            <Input search placeholder="搜索" @on-change="searchHis" v-model="tableHis.searchStr"/>
          </iCol>
        </Row>
        <Row style="margin-top: 5px;display: block">
          <Table
              highlight-row
              :columns="tableHis.headers"
              :data="tableHis.body"
              :show-header="false"
              :row-class-name="rowClassName"
              height="500"
              @on-row-click="showData"
              style="margin: 5px"
          >
            <template
                slot-scope="{ row, index }"
                slot="action"
                style="padding-left: 0; padding-right: 0"
            >
              <a
                  v-clipboard:copy="getShareUrl(row, index)"
                  v-clipboard:success="shareUrl"
                  v-clipboard:error="shareUrlError"
              ><strong style="white-space: nowrap;">分享</strong></a
              >
            </template>
          </Table>
        </Row>
      </div>
    </Modal>

  </div>
</template>

<script>
import Vue from "vue";
import VueClipboard from "vue-clipboard2";
import {
  getRepeaterGoData,
  getRepeaterHistoryData,
  postRepeaterShareAuthID,
  getRepeaterGetData
} from "@/utils/api";
import {
  getEncodeVar,
  diff_prettyHtml,
  makeAuthID,
  evalRange
} from "@/utils/tools";
import DiffMatchPatch from 'diff-match-patch';

Vue.use(VueClipboard);
const IGNORE_KEYS = ["_iid", "_version_", "mkVersion", "_ab_test_", "_net_", "_uid_"];
const FLAG_STR = "§";
const dmp = new DiffMatchPatch();
DiffMatchPatch.DIFF_DELETE = 1;
DiffMatchPatch.DIFF_INSERT = 1;
DiffMatchPatch.DIFF_EQUAL = 0;

export default {
  name: "Index",
  data: () => {
    return {
      tableHis: {
        headers: [
          {
            title: "历史记录",
            key: "text",
          },
          {
            title: "操作",
            slot: "action",
            width: 50,
          },
        ],
        body: [],
        search: [],
        searchStr: "",
        allData: {
          body: [],
          search: [],
        },
      },
      query: {
        request: "",
        host: "",
        port: "",
        ishttps: false,
        concurrent_num: 0,
        keepua: true,
        type: "pitchfork",
        payload: [],
      },
      request: "",
      response: "",
      selectDataList: [],
      resultCollapse: "",
      concurrentModal: {
        show: false,
        table: {
          headers: [
            {
              title: "id",
              key: "num_id",
              width: 60,
            },
            {
              title: "status",
              key: "status_code",
              width: 60,
            },
            {
              title: "payload",
              key: "payload",
              width: 120,
            },
            {
              title: "response",
              slot: "content",
            },
          ],
          body: [],
        },
      },
      selectFlag: {
        startIdx: 0,
        endIdx: 0,
      },
      encodeTypeList: ["sniper", "battering ram", "pitchfork", "cluster bomb"],
      repeaterTestModal: {
        show: false,
        vars: "",
        dest: "",
        rawDest: {},
        rawVars: [],
        rawDivHeight: "100px",
        simpleModel: false,
        title: "Payload配置",
        preShow: false,
        preRaw: "",
      },
      modalHistory: false,
      shareIdAuthCodeDict: {},
    }
  },
  methods: {
    strToLowerCase: (str) => {
      return str ? str.toLowerCase() : "";
    },
    showRepeaterHistory: function () {
      getRepeaterHistoryData({}).then((resp) => {
        this.tableHis.body = [];
        for (let e of resp.data.data.history) {
          let d = e.request;
          let body = {
            text: d.scheme + "://" + d.host + d.path,
            raw: e,
          };
          this.tableHis.body.push(body);
          let search =
              this.strToLowerCase(d.scheme) +
              "://" +
              this.strToLowerCase(d.host) +
              this.strToLowerCase(d.path) +
              this.strToLowerCase(d.response) +
              this.strToLowerCase(d.content);

          this.tableHis.search.push(search);
          this.tableHis.allData.body.push(body);
          this.tableHis.allData.search.push(search);
        }
      });
    },
    searchGo: function () {
      let _this = this;
      let req_body = JSON.parse(JSON.stringify(this.query));
      _this.response = "";
      req_body.request = this.request;

      getRepeaterGoData(req_body)
          .then((resp) => {
            if (_this.query.concurrent_num > 0) {
              _this.concurrentModal.show = true;
              _this.concurrentModal.table.body = resp.data.data.data;
            } else {
              this.showRepeaterHistory();
              this._showResponseData(resp.data.data.response);
            }
          })
          .catch(function (err) {
            if (err.response) {
              if (err.response.status < 500) {
                _this.$Notice.error({
                  title: "请求错误，注意检查请求参数",
                });
              } else {
                _this.$Notice.error({
                  title: "服务端发生未知错误,状态码: " + err.response.status,
                });
              }
            } else {
              _this.$Notice.error({
                title: "未知请求异常",
              });
            }
          });
    },
    requestContentFormat: function (type) {
      if (!this.request || this.request.length < 1) {
        return;
      }
      let result = this.request.split("\n");
      let content = result[result.length - 1];
      if (content[0] === "{" && type === "json") {
        return;
      } else if (content[0] !== "{" && type === "raw") {
        return;
      }
      if (type === "json") {
        let tmp = new URLSearchParams(content);
        content = {};
        for (let key of tmp.keys()) {
          if (IGNORE_KEYS.includes(key)) {
            continue;
          }
          content[key] = tmp.get(key);
        }
        content = JSON.stringify(content);
      } else if (type === "raw") {
        content = JSON.parse(content);
        for (let key of IGNORE_KEYS) {
          if (key in content) {
            delete content[key];
          }
        }
        content = new URLSearchParams(content).toString();
      }
      result[result.length - 1] = content;
      for (let idx = 0; idx < result.length; idx++) {
        let line = result[idx];
        if (!line) {
          continue;
        }
        line = line.split(":");
        let key = line[0].toLowerCase().trim();
        if (key !== "content-type") {
          continue;
        }
        for (let i = 1; i < line.length; i++) {
          let v = line[i].toLowerCase().trim();
          if (["application/x-www-form-urlencoded", "application/json"].includes(v)) {
            line[i] = type === "raw" ? "application/x-www-form-urlencoded" : "application/json";
          }
        }
        result[idx] = line.join(":");
      }
      this.request = result.join("\n");
    },
    addFlag: function () {
      let point = this.$refs.requestEl.$el.children[0].selectionStart;
      let selectFlag =
          this.selectFlag.startIdx || this.selectionEnd ? this.selectFlag : {startIdx: point, endIdx: point};
      let startStr = this.request.slice(0, selectFlag.startIdx);
      let subStr = this.request.slice(selectFlag.startIdx, selectFlag.endIdx);
      let endStr = this.request.slice(selectFlag.endIdx);
      this.request = `${startStr}${FLAG_STR}${subStr}${FLAG_STR}${endStr}`;
    },
    clearFlag: function () {
      this.request = this.request.split(FLAG_STR).join("");
    },
    showPayload() {
      let _this = this;
      if ([..._this.request].filter((item) => item === FLAG_STR).length % 2) {
        _this.$Message.error(`缺少闭合标识符: ${FLAG_STR}`);
        return;
      }
      if (_this.query.type === "pitchfork" || _this.query.type === "cluster bomb") {
        _this.repeaterTestModal.simpleModel = false;
      } else {
        _this.repeaterTestModal.simpleModel = true;
      }
      _this.repeaterTestModal.title = `Payload配置 (${_this.query.type})`;
      _this.repeaterTestModal.show = true;
      let vars = [];
      try {
        vars = getEncodeVar(_this.request);
      } catch (e) {
        _this.$Message.error(e);
        console.error(e);
      }
      _this.repeaterTestModal.rawVars = vars;
      _this.repeaterTestModal.vars = vars.join("\n");
      _this.repeaterTestModal.rawDivHeight = _this.$refs.repeaterTestModal.children[0].children[0].style.height;
    },
    openNewUrl: function (url) {
      window.open(url, "_blank")
    },
    getDifferHtml: function (oldStr, newStr) {
      const diff = dmp.diff_main(oldStr, newStr);
      dmp.diff_cleanupSemantic(diff);
      return diff_prettyHtml(diff);
    },
    searchHis: function () {
      let result = {
        body: [],
        search: [],
      };
      let str = this.strToLowerCase(this.tableHis.searchStr);
      if (!str) {
        this.tableHis.body = this.tableHis.allData.body;
        this.tableHis.search = this.tableHis.allData.search;
        return;
      }
      for (let idx = 0; idx < this.tableHis.allData.search.length; idx++) {
        let d = this.tableHis.allData.search[idx];
        if (d && d.includes(str)) {
          result.body.push(this.tableHis.allData.body[idx]);
          result.search.push(d);
        }
      }
      this.tableHis.body = result.body;
      this.tableHis.search = result.search;
    },
    showData: function (row, idx) {
      this.selectDataList = []
      let data = row.raw;
      this.selectIdx = idx;
      this._showRequestData(data.request);
      this._showResponseData(data.response);
    },
    getShareUrl: function (row) {
      //生成随机id
      let authId = makeAuthID(24);
      let requestId = row.raw.request._id;
      let shareUri = `${window.location.origin.toString()}/#/repeater?id=${requestId}&auth_code=${authId}`;
      this.shareIdAuthCodeDict[shareUri] = {"authId": authId, "requestId": requestId}
      return shareUri
    },
    shareUrl: function (e) {
      let sharData = this.shareIdAuthCodeDict[e.text]
      if (sharData) {
        postRepeaterShareAuthID(sharData["requestId"], sharData["authId"])
            .then(() => {
            })
            .catch(() => {
              this.$Message.warning("ShareAuthCode上传失败");
            });
      }
      this.$Notice.open({
        title: "分享链接",
        desc: e.text.replace("&auth_code", "&auth_code\n"),
      });
    },
    shareUrlError: function () {
      this.$Notice.error({
        title: "分享链接失败",
      });
    },
    bodyRequestSelectEvent: function (e) {
      this.selectFlag = {
        startIdx: e.target.selectionStart,
        endIdx: e.target.selectionEnd,
      };
    },
    bodyResponseSelectEvent: function () {
      this.selectFlag = {
        startIdx: 0,
        endIdx: 0,
      };
    },
    _generateTitle: function (requestData, responseData) {
      let numId = requestData.num_id
      let payload = requestData.payload
      let length = responseData.content.length
      return `编号:${numId}  Payload:${payload}  长度:${length}`
    },
    _convertRequestResult: function (data) {
      let result = [
        `${data.method} ${data.path} ${data.http_version}`,
        `Host: ${data.host}${data.port ? ":" + data.port : ""}`,
      ];
      for (let k in data.headers) {
        if (k === "Host") {
          continue;
        }
        result.push(k + ": " + data.headers[k]);
      }
      result.push("");
      result.push(data.content.trim());
      return result.join("\n");
    },
    _convertResponseResult: function (data) {
      if (!data || !data.headers) {
        this.response = "";
        return;
      }
      let result = [data.http_version + " " + data.status_code + " " + data.reason];
      for (let k in data.headers) {
        result.push(k + " : " + data.headers[k]);
      }
      result.push("");
      result.push(data.content);
      return result.join("\n");
    },
    _showRequestData: function (data) {
      this.request = this._convertRequestResult(data)

      this.query.host = data.host;
      this.query.port = data.port;
      this.query.ishttps = Boolean(this.strToLowerCase(data.scheme) === "https");
    },
    _showResponseData: function (data) {
      this.response = this._convertResponseResult(data)
    },
    rowClassName() {
      return 'table-history-record-row';
    },
    preShowPlayload(opt) {
      let _this = this;
      if (opt === "cancel") {
        _this.repeaterTestModal.preShow = false;
        if (_this.repeaterTestModal.simpleModel) {
          _this.repeaterTestModal.dest = _this.repeaterTestModal.preRaw;
        } else {
          for (let v of _this.repeaterTestModal.rawVars) {
            _this.repeaterTestModal.rawDest[v] = _this.repeaterTestModal.preRaw[v];
          }
        }
        return;
      }
      _this.repeaterTestModal.preShow = true;
      try {
        _this.setPlayload();
      } catch (e) {
        _this.$Message.error(`参数错误 ${e}`);
        _this.repeaterTestModal.preShow = false;
      }
      if (_this.repeaterTestModal.simpleModel) {
        _this.repeaterTestModal.preRaw = _this.repeaterTestModal.dest;
        _this.repeaterTestModal.dest = _this.query.payload[0].join("\n");
      } else {
        _this.repeaterTestModal.preRaw = Vue.util.extend({}, _this.repeaterTestModal.rawDest);
        for (let idx = 0; idx < _this.repeaterTestModal.rawVars.length; idx++) {
          _this.repeaterTestModal.rawDest[_this.repeaterTestModal.rawVars[idx]] = _this.query.payload[
              idx
              ].join("\n");
        }
      }
    },
    setPlayload() {
      let _this = this;
      let payload = [];
      if (_this.repeaterTestModal.simpleModel) {
        payload = [getEncodeVar(_this.repeaterTestModal.dest, FLAG_STR, true)];
      } else {
        for (let v of _this.repeaterTestModal.rawVars) {
          payload.push(getEncodeVar(_this.repeaterTestModal.rawDest[v], FLAG_STR, true));
        }
      }
      for (let [idx, lines] of Object.entries(payload)) {
        for (let [i, line] of Object.entries(lines)) {
          line = evalRange(line);
          if (line.trim().startsWith(FLAG_STR)) {
            line = line.trim().split(FLAG_STR).join("");
            try {
              line = eval(line)();
              if (line.constructor.name === "Array") {
                line = line.join("\n");
              } else if (line.constructor.name !== "String") {
                _this.$Message.error(
                    `返回值内容仅支持字符串和数组,错误段: \n${JSON.stringify(line)} \n`
                );
              }
            } catch (e) {
              throw `参数错误 ${e}`;
            }
          }
          lines[i] = line;
        }
        payload[idx] = lines.filter((item) => item.trim() !== "");
      }
      _this.query.payload = payload;
    },
  },
  mounted() {
    if (this.$route.query.id) {
      let auth_code = this.$route.query.auth_code
      let queryCondition = {"id": this.$route.query.id}
      if (auth_code) {
        queryCondition['auth_code'] = auth_code
      }
      getRepeaterGetData(queryCondition).then((resp) => {
        this._showRequestData(resp.data.data[0].request);
        this._showResponseData(resp.data.data[0].response);
        let convertList = []
        let repeaterList = resp.data.data
        if (repeaterList.length > 0) {
          repeaterList.forEach((item, number) => {
            if (number > 0) {
              let routerConf = this.$router.resolve({
                name: 'repeater', query: {id: item.request._id}
              })
              convertList.push({
                "title": this._generateTitle(item.request, item.response),
                "url": routerConf.href,
                "request": this._convertRequestResult(item.request),
                "response": this._convertResponseResult(item.response)
              })
            }
          })
        }
        this.selectDataList = convertList
      });
    }
    this.showRepeaterHistory();
  }
}
</script>

<style>
.ivu-table .table-history-record-row div {
  padding: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
}
</style>

<style scoped>
.ivu-btn-primary {
  background-color: #547EFF;
}
</style>