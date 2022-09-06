<template>
  <div class="layout">
    <Row style="margin: 10px;padding-left: 13px;">
      <Input
          v-model="query.ip"
          placeholder="ip"
          style="max-width: 15%"
          @on-change="setLoggerStorage"
          @on-blur="search"
      />
      <Input
          v-model="query.filter"
          @on-blur="tableFilterEvent"
          placeholder="filter"
          style="max-width: 15%;margin-left: 10px"
      />
      <Button
          @click="connectWebSocket('disconnect')"
          type="text"
          size="small"
          style="background: #19be6b; margin-left: 10px; height:32px;width:70px;color:#FFFFFF;"
          v-if="connectStatus"
      >已连接
      </Button
      >
      <Button
          @click="connectWebSocket('connect')"
          type="text"
          size="small"
          style="background: #ed4014; margin-left: 10px; height:32px;width:70px;color:#FFFFFF;"
          v-else
      >未连接
      </Button>
      <Button
          type="primary"
          size="small"
          class="search-btn"
          :style="{ margin: '0 10px ', 'background-color':'#547EFF', height:'32px', 'width':'60px',}"
          @click="clearScreen()">
        <Icon type="search"/>
        清屏
      </Button>
    </Row>
    <Row style="margin: 10px;padding-left: 13px;">
      <Table
          highlight-row
          :columns="tableHeaders"
          :data="tableBody"
          :row-class-name="rowClassName"
          height="400"
          @on-row-click="showDetailData"
          @on-column-width-resize="resizeTableColumn"
          border
      >
        <template slot-scope="{ row, index }" slot="action">
          <a @click="optAtom(row, index)" style="margin-right: 10px"
          ><strong>重放</strong></a>
          <a
              v-clipboard:copy="getShareUrl(row, index)"
              v-clipboard:success="shareUrl"
              v-clipboard:error="shareUrlError"
          ><strong>分享</strong></a>
        </template>
        <template slot-scope="{ row }" slot="desc">
          <Input
              v-model="row.desc"
              readonly
              @on-click="editorNotes($event, row)"
              @on-blur="changeNotes($event, row)"
              @on-enter="changeNotes($event, row)"
              icon="ios-create-outline"
          />
        </template>
      </Table>
    </Row>
    <Row style="margin: 10px;padding-left: 13px">
      <iCol span="12">
        <Card :bordered="true">
          <div slot="title" :style="{ height: '10px' }">
            <span style="float: left;">Request</span>
            <Row style="float: left; margin-left:20px;">
              <Button type="primary" size="small" v-if="request_show_flag" @click="request_show_flag=true"
                      style="border-radius:0; border-bottom: none; background-color:#547EFF;">优化
              </Button>
              <Button size="small" @click="request_show_flag=true" style="border-radius:0; border-bottom: none;" v-else>
                优化
              </Button>

              <Button type="primary" size="small" v-if="!request_show_flag"
                      @click="request_show_flag=false"
                      style="border-radius:0; border-bottom: none;background-color:#547EFF;">原始
              </Button>
              <Button size="small"
                      @click="request_show_flag=false" style="border-radius:0; border-bottom: none;" v-else>原始
              </Button>
            </Row>
            <div style="float: right">
              <a type="primary" @click="toRepeater">重放</a>
            </div>
          </div>
          <div>
            <Input type="textarea" v-if="request_show_flag" v-model="request" readonly :autosize="{ minRows: 6 }"/>
            <Input type="textarea" v-else v-model="request_raw" readonly :autosize="{ minRows: 6 }"/>
          </div>

        </Card>
      </iCol>
      <iCol span="12">
        <Card :bordered="true">
          <div slot="title" :style="{ height: '10px' }">
            <span style="float: left;">Response</span>
            <Row style="float: left; margin-left:20px;">
              <Button type="primary" size="small" v-if="response_show_flag" @click="response_show_flag=true"
                      style="border-radius:0; border-bottom: none;background-color:#547EFF;">优化
              </Button>
              <Button size="small" @click="response_show_flag=true" style="border-radius:0; border-bottom: none;"
                      v-else>优化
              </Button>

              <Button type="primary" size="small" v-if="!response_show_flag"
                      @click="response_show_flag=false"
                      style="border-radius:0; border-bottom: none;background-color:#547EFF;">原始
              </Button>
              <Button size="small"
                      @click="response_show_flag=false" style="border-radius:0; border-bottom: none;" v-else>原始
              </Button>
            </Row>
          </div>
          <div>

            <Input type="textarea" v-if="response_show_flag" v-model="response" readonly
                   :autosize="{ minRows: 6 }"/>
            <Input type="textarea" v-else v-model="response_raw" readonly :autosize="{ minRows: 6 }"/>
          </div>
        </Card>
      </iCol>
    </Row>
  </div>
</template>

<script>
import io from "socket.io-client";
import Vue from "vue";
import VueClipboard from "vue-clipboard2";
import {timestampToString} from "@/utils/logger";
import {
  postEditLogerDesc,
  postRepeaterShareAuthID,
} from "@/utils/api";
import {makeAuthID} from "@/utils/tools";

Vue.use(VueClipboard);

export default {
  name: "LoggerIndex",
  data() {
    return {
      tableHeaders: [
        {
          title: "Domain",
          key: "domain",
          width: "300",
          resizable: true,
        },
        {
          title: "Path",
          key: "path",
          width: "400",
          resizable: true,
        },
        {
          title: "Time",
          key: "time",
          width: "160",
          resizable: true,
        },
        {
          title: "Method",
          key: "method",
          width: "100",
          resizable: true,
        },
        {
          title: "status",
          key: "status",
          width: "100",
          resizable: true,
          filters: [
            {
              label: '5XX',
              value: "5"
            },
            {
              label: '4XX',
              value: "4"
            },
            {
              label: '3XX',
              value: "3"
            },
            {
              label: '2XX',
              value: "2"
            },
            {
              label: '1XX',
              value: "1"
            }
          ],
          filterMethod(value, row) {
            return String(row.status).startsWith(value);
          },
        },
        {
          title: "length",
          key: "length",
          width: "80",
          resizable: true,
        },
        {
          title: "描述",
          slot: "desc",
          align: "center",
          width: "120",
          resizable: true,
        },
        {
          title: "操作",
          slot: "action",
          align: "center",
          width: "120",
          resizable: true,
        },
      ],
      showTableReqIds: [],
      tableBody: [],
      wsFullRequest: [],
      wsFullMap: {},
      query: {
        ip: "",
        start_time: "",
        end_time: "",
        filter: "",
      },
      select_idx: "",
      socket_handler: "",
      request: "",
      response: "",
      request_raw: "",
      response_raw: "",
      request_show_flag: true,
      response_show_flag: true,
      choicesRow: {},
      connectStatus: false,
      shareIdAuthCodeDict: {},
      splitValue: 0.5,
    }
  },
  methods: {
    setLoggerStorage() {
      localStorage.setItem("loggerPage", JSON.stringify(this.query));
    },
    rowClassName() {
      return 'table-logger-ws-row';
    },
    showTable: function (data) {
      if (this.tableFilter(data)) {
        return;
      }
      let row = this.formatTableRow(data);
      let idx = this.showTableReqIds.indexOf(row.raw_idx);
      if (idx > -1) {
        this.tableBody[idx] = row;
      } else {
        this.showTableReqIds.unshift(row.raw_idx);
        this.tableBody.unshift(row);
      }
    },
    connectWebSocket: function (action) {
      let that = this;
      if (action === "disconnect") {
        if (that.socket_handler.connected) {
          that.$Notice.info({
            title: "断开连接",
          });
          that.socket_handler.close();
        }
        that.connectStatus = false;
        that.socket_handler = "";
        return;
      }
      if (that.socket_handler && that.socket_handler.connected) {
        return;
      }
      const socket_handler = io("/api/logerws", {
        enablesXDR: true,
        path: "/api/logerws",
        transports: ["websocket"],
        enabledTransports: ["ws", "wss"],
      });
      socket_handler.on("connect", function () {
        that.socket_handler = socket_handler;
        that.socket_handler.emit("set_filter", that.getQuery());
        that.socket_handler.emit("get");
        socket_handler.on("get", function (data) {
          if (data.status === "closed") {
            that.connectWebSocket("disconnect");
            return;
          }
          try {
            if (data.request) {
              if (Object.prototype.hasOwnProperty.call(that.wsFullMap, data.request._id)) {
                data.response = that.wsFullMap[data.request._id]["response"];
                that.wsFullMap[data.request._id] = data;
              } else {
                that.wsFullRequest.unshift(data.request._id);
                that.wsFullMap[data.request._id] = data;
              }
            }
            if (data.response && Object.keys(data.response).length) {
              that.wsFullMap[data.response.req_id]["response"] = data.response;
              if (!data.request) {
                for (let idx = 0; idx < that.wsFullRequest.length; idx++) {
                  if (that.wsFullRequest[idx] === data.response.req_id) {
                    that.tableBody[idx] = that.wsFullMap[data.response.req_id];
                    that.tableBody[idx]["raw_idx"] = idx;
                    that.tableBody[idx]["status"] = data.response.status_code;
                    that.tableBody[idx]["length"] = data.response.content.length;
                  }
                }
              }
              data.request = that.wsFullMap[data.response.req_id].request;
            }
            that.showTable(data);
          } catch (err) {
            console.log(err);
          }
          if (that.wsFullRequest.length >= 500 && that.wsFullRequest.length % 100 === 0) {
            that.$Message.warning(`浏览器缓存数据已经达到${that.wsFullRequest.length}, 建议清屏!!!`);
          }
        });
        that.$Notice.info({
          title: "连接成功",
        });
        that.connectStatus = true;
      });

      socket_handler.on("error", function () {
        that.connectWebSocket("disconnect");
      });
      socket_handler.on('disconnect', function () {
        that.connectWebSocket("disconnect");
      });
      if ((that.socket_handler && that.socket_handler.disconnected) || that.socket_handler) {
        that.connectWebSocket("disconnect");
      }
      return socket_handler;
    },
    tableFilter: function (data) {
      let filterStr = this.query.filter + "";
      if (!filterStr) {
        return false;
      }
      return !JSON.stringify(data).includes(filterStr);
    },
    formatTableRow(data) {
      let row = {
        domain: data.request.host,
        path: data.request.path,
        time: timestampToString(data.request.timestamp_start),
        method: data.request.method,
        status: "",
        length: -1,
        desc: data.request.describe || "",
        raw_idx: data.request._id,
        _highlight: this.select_idx === data.raw_idx,
      };
      if (data.response && Object.keys(data.response).length) {
        row.status = data.response.status_code;
        row.length = data.response.content.length;
      }
      return row;
    },
    resizeTableColumn: function (newWidth, oldWidth, column) {
      this.setLoggerTableConfig(column.title, parseInt(newWidth))
    },
    setLoggerTableConfig(title, width) {
      let tableConfig = {}
      let tableConfigStr = localStorage.getItem("LoggerTableConfig");
      if (tableConfigStr != null) {
        tableConfig = JSON.parse(tableConfigStr)
      }
      tableConfig[title] = width
      localStorage.setItem("LoggerTableConfig", JSON.stringify(tableConfig));
    },
    tableFilterEvent: function () {
      let tableBody = [];
      let tableIds = [];
      for (let pk of this.wsFullRequest) {
        if (this.tableFilter(this.wsFullMap[pk])) {
          continue;
        }
        let row = this.formatTableRow(this.wsFullMap[pk]);
        tableIds.push(row.raw_idx);
        tableBody.push(row);
      }
      this.showTableReqIds = tableIds;
      this.tableBody = tableBody;
    },
    clearScreen() {
      this.tableBody = [];
      this.wsFullRequest = [];
      this.wsFullMap = {};
    },
    getRawData: function (idx) {
      return this.wsFullMap[idx];
    },
    showDetailData: function (row) {
      this.select_idx = row.raw_idx;
      this.tableBody.map((item) => {

        item._highlight = row.raw_idx === item.raw_idx;
      });
      let data = this.getRawData(row.raw_idx);
      if (!data || !Object.keys(data).length) {
        console.error(data);
        this.$Message.warning("数据有误,无法展示");
        return;
      }
      this.choicesRow = data;
      this._showRequestData(data.request);
      this._showRequestRawData(data.request);
      this._showResponseData(data.response);
      this._showResponseRawData(data.response);
    },
    _showRequestData: function (data) {
      let result = [data.method + " " + data.path + " " + data.http_version, "Host: " + data.host];
      for (let k in data.headers) {
        if (k === "Host") {
          continue;
        }
        result.push(k + ": " + data.headers[k]);
      }
      result.push("");
      result.push(data.pretty_text);
      this.request = result.join("\n");
    },
    _showRequestRawData: function (data) {
      let result = [data.method + " " + data.path + " " + data.http_version, "Host: " + data.host];
      for (let k in data.headers) {
        if (k === "Host") {
          continue;
        }
        result.push(k + ": " + data.headers[k]);
      }
      result.push("");
      result.push(data.content);
      this.request_raw = result.join("\n");
    },
    _showResponseData: function (data) {
      if (!data) {
        this.response = "";
        return;
      }
      let result = [data.http_version + " " + data.status_code + " " + data.reason];
      for (let k in data.headers) {
        result.push(k + " : " + data.headers[k]);
      }
      result.push("");
      result.push(data.pretty_text);
      this.response = result.join("\n");
      this.response = this.response.trim();
    },
    _showResponseRawData: function (data) {
      if (!data) {
        this.response_raw = "";
        return;
      }
      let result = [data.http_version + " " + data.status_code + " " + data.reason];
      for (let k in data.headers) {
        result.push(k + " : " + data.headers[k]);
      }
      result.push("");
      result.push(data.content);
      this.response_raw = result.join("\n");
      this.response_raw = this.response_raw.trim();
    },
    optAtom: function (row) {
      let data = this.getRawData(row.raw_idx);
      if (!data || !data.request || !Object.keys(data.request).length) {
        return "";
      }
      window.open("/#/repeater?id=" + data.request._id);
    },
    editorNotes: function (e, row) {
      let data = this.getRawData(row.raw_idx);
      if (!data || !data.request || !Object.keys(data.request).length || !data.request._id) {
        this.$Message.warning("本条数据有误，无法编辑");
        return "";
      }
      e.target.parentNode.children[1].readOnly = false;
      this.$Message.info("编辑:" + data.request.host);
    },
    changeNotes: function (e, row) {
      if (e.target.parentNode.children[1].readOnly) {
        return;
      }
      e.target.parentNode.children[1].readOnly = true;
      let data = this.getRawData(row.raw_idx);

      if (!data || !data.request || !Object.keys(data.request).length || !data.request._id) {
        this.$Message.warning("本条数据有误，无法编辑");
        return "";
      }
      let _this = this;
      try {
        postEditLogerDesc({
          id: data.request._id,
          describe: row.desc,
        })
            .then(() => {
              this.$Notice.info({
                title: "保存成功",
              });
              _this.wsFullMap[row.raw_idx].request.describe = row.desc;
            })
            .catch((err) => {
              this.$Notice.error({
                title: "保存失败,服务异常",
                desc: err
              });
            });
      } catch (e) {
        this.$Message.warning(e);
      }
    },
    getShareUrl: function (row) {
      let data = this.getRawData(row.raw_idx);
      if (!data || !data.request || !Object.keys(data.request).length) {
        return "";
      }
      //生成随机id
      let authId = makeAuthID(24);
      let requestId = data.request._id
      let shareUri = `${window.location.origin.toString()}/#/repeater?id=${requestId}&auth_code=${authId}`
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
    toRepeater() {
      if (this.choicesRow.request && this.choicesRow.request._id) {
        window.open(`/#/repeater?id=${this.choicesRow.request._id}`);
      }
    },
    getLoggerTableConfig() {
      let tableConfigStr = localStorage.getItem("LoggerTableConfig");
      let tableConfig = JSON.parse(tableConfigStr)
      if (tableConfig === null) {
        return
      }
      this.tableHeaders.forEach(item => {
        if (item.title in tableConfig) {
          item.width = tableConfig[item.title]
        }
      })
    },
    getQuery: function () {
      const timeFields = ["start_time", "end_time"];
      let query = JSON.parse(JSON.stringify(this.query));
      for (let field of timeFields) {
        let value = query[field];
        if (value) {
          value = new Date(value);
          query[field] = parseInt(value.getTime() / 1000);
        }
      }
      return query;
    },
    search() {
      if (!this.socket_handler || !this.socket_handler.connected) {
        this.socket_handler = this.connectWebSocket();
      } else {
        this.socket_handler.emit("set_filter", this.getQuery());
        this.socket_handler.emit("get");
      }
    },
  },
  mounted() {
    this.setLoggerStorage();
    this.getLoggerTableConfig();
  },
  beforeDestroy() {
    if (this.socket_handler) {
      this.socket_handler.close();
    }
  },
}
</script>

<style>
.ivu-table .table-logger-ws-row td {
  height: 18px;
  line-height: 1.2;
}
</style>

<style scoped>
.ivu-card >>> .ivu-card-head {
  border-bottom: none;
}

.ivu-card >>> .ivu-card-body {
  padding: 0 16px 16px 16px;
}
</style>