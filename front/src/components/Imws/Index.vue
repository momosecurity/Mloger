<template>
  <div class="layout">
    <Row style="padding: 5px;margin-bottom: 5px" :gutter="10">
      <iCol span="17">
        <Input
            v-model="query.client_ip"
            placeholder="请输入客户端IP"
            style="width: 200px"
        />
        <Select v-model="query.type" style="width: 120px; margin-left: 10px">
          <Option v-for="[k, v] of Object.entries(typeMap)" :key="k" :value="k">{{ v }}</Option>
        </Select>
        <Input
            v-model="query.filter"
            @on-blur="tableFilterEvent"
            placeholder="过滤字符串"
            style="max-width: 15%;margin-left: 10px"
        />
        <Button type="primary" class="search-btn" style="margin-left: 10px;background: #ed4014; border:none"
                @click="search">
          <div v-if="!this.wsHandler.status">
            未连接
          </div>
          <div v-else>
            已连接
          </div>
        </Button>
        <Button type="primary" class="search-btn" :style="{ margin: '0 10px ' }" @click="clearScreen">
          清屏
        </Button>
      </iCol>

    </Row>
    <Row :gutter="10">
      <iCol span="7">
        <LinkTable :linkData="linkData" :ip="query.ip" @showConnDetail="showConnDetail"></LinkTable>
      </iCol>
      <iCol span="10">
        <Card :bordered="true">
          <p slot="title">消息列表</p>
          <p slot="extra">
            <span>条数: {{ table.body.length }}</span>
          </p>
          <Table
              highlight-row
              :columns="table.headers"
              :data="table.body"
              @on-row-click="showDetail"
              height="590"
          ></Table>
        </Card>
      </iCol>
      <iCol span="7">
        <Card :bordered="true">
          <p slot="title">
            <span style="margin-right: 10px">消息详情</span>
            <Checkbox size="small" v-model="showMsgDetail.isShowHex">HEX</Checkbox>
          </p>
          <p slot="extra">
            <span>Direction: {{ showMsgDetail.type }}</span>
          </p>
          <Input
              type="textarea"
              v-model="showMsgDetail.text"
              :autosize="{
                            minRows: 14,
                            maxRows: 14,
                        }"
              @on-change="updateHexText"
          />
        </Card>
        <Row type="flex" justify="end" style="margin-top:5px;margin-bottom:5px;">
          <div style="display: inline-flex; margin-right:10px">
            <span style="width: 60px; margin-top: 7px">并发数:</span>
            <Input v-model="process_cnt" placeholder="并发数" style="width: 40px"/>
          </div>
          <Button
              class="search-btn action-btn"
              @click="repeaterGo('send')"
              :style="{ 'margin-right': '10px', 'color':'#547EFF', 'border-color':'#547EFF' }"
              :disabled="msgDetail.actionStatus"
              :loading="msgDetail.actionStatus"
          >
            <Icon type="search"/>
            发送
          </Button>

          <Button
              class="search-btn action-btn"
              @click="repeaterGo('receive')"
              :style="{ 'margin-right': '10px', 'background':'#547EFF','color':'#FFFFFF', }"
              :disabled="msgDetail.actionStatus"
              :loading="msgDetail.actionStatus"
          >
            <Icon type="search"/>
            接收
          </Button>
        </Row>
        <Card :bordered="true" v-if="showMsgDetail.isShowHex">
          <p slot="title">HEX</p>
          <Input
              type="textarea"
              v-model="showMsgDetail.hex_text"
              :autosize="{ minRows: 14, maxRows: 14 }"
              @on-change="updateText"
          />
        </Card>
      </iCol>
    </Row>
  </div>
</template>

<script>
import io from "socket.io-client";
import {imwsRepeaterGo, interceptOpImws, interceptImws} from "@/utils/api";

import LinkTable from "./components/LinkTable";

const HEX_CH = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "A", "B", "C", "D", "E", "F"];

export default {
  name: "imws-index",
  components: {
    LinkTable,
  },
  data() {
    return {
      wsHandler: {
        status: false,
        sock: "",
      },
      typeMap: {
        all: "全部",
        tcp: "tcp",
        websocket: "websocket"
      },
      query: {
        filter: "",
        type: "all",
        ip: "",
        showConnPk: "",
      },
      process_cnt: 0,
      linkData: {},
      table: {
        headers: [
          {
            title: "Message",
            key: "content",
            align: "center",
            render: (h, params) => {
              return h("span", params.row.content.slice(0, 150));
            },
          },
          {
            title: "Direction",
            key: "direction",
            align: "center",
            width: "110",
          },
          {
            title: "length",
            key: "length",
            align: "center",
            width: "80",
          },
        ],
        body: [],
        filter: "",
        select_idx: "",
      },
      msgData: {},
      msgDataIdx: {},
      showMsgDetail: {
        pk: "",
        text: "",
        hex_text: "",
        isShowHex: false,
        type: "",
        conn_id: "",
      },
      msgDetail: {
        pk: "",
        text: "",
        show: true,
        filterStatus: false,
        actionStatus: false,
      },
    }
  },
  methods: {
    getQuery: function (type = "filter") {
      if (type === "sock") {
        return {
          ip: this.query.ip,
          type: this.query.type,
        };
      }
      return {}
    },
    tableFilterEvent: function () {
      this.table.filter = this.query.filter;
      this.showConnDetail(this.query.showConnPk);
    },
    isTableFilter: function (item) {
      let msg = item.content || "";
      return msg.includes(this.table.filter);
    },
    webSocket: function (type) {
      let _this = this;
      if (type === "disconnect") {
        if (_this.wsHandler.sock !== "") {
          _this.wsHandler.sock.close();
          _this.wsHandler.status = _this.wsHandler.sock.connected;
          _this.wsHandler.sock = "";
        }
        this.$Notice.info({
          title: "断开连接",
        });
        return;
      }
      if (_this.wsHandler.sock && _this.wsHandler.sock.connected) {
        return;
      }

      const sock = io("/api/imws", {
        enablesXDR: true,
        path: "/api/logerws",
        transports: ["websocket"],
        enabledTransports: ["ws", "wss"],
      });

      sock.on("connect", function () {
        _this.wsHandler.sock = sock;
        sock.emit("set_filter", _this.getQuery("sock"));
        sock.emit("get");
        sock.on("get_conn", function (data) {
          _this.linkData[data._id] = {from_dt: new Date().getTime(), ...data};
        });
        sock.emit("get_mes");
        sock.on("get_mes", function (data) {
          data.length = (data.content || "").length;
          if (data.conn_id in _this.msgData) {
            let idx = _this.msgDataIdx[data.conn_id].indexOf(data._id);
            if (idx < 0) {
              _this.msgData[data.conn_id].push(data);
              _this.msgDataIdx[data.conn_id].push(data._id);
            } else {
              _this.msgData[data.conn_id][idx] = data;
            }
          } else {
            _this.msgData[data.conn_id] = [data];
            _this.msgDataIdx[data.conn_id] = [data._id];
          }
          _this.refreshConnDetail(data);
        });

        if (sock.connected) {
          _this.wsHandler.status = sock.connected;
          _this.$Notice.info({
            title: "连接成功",
          });
        } else {
          _this.$Notice.error({
            title: "连接异常",
          });
        }
      });

      sock.on("reconnect", function () {
        _this.wsHandler.sock !== "" ? _this.wsHandler.sock.close() : "";
        _this.wsHandler.status = false;
        _this.wsHandler.sock = "";
        _this.webSocket();
      });
      sock.on("error", function () {
        _this.webSocket("disconnect");
      });
      if ((_this.wsHandler.sock && _this.wsHandler.sock.disconnected) || _this.sock) {
        _this.webSocket("disconnect");
      }
    },
    showConnDetail: function (conn_id) {
      let _this = this;
      _this.query.showConnPk = conn_id;
      _this.showMsgDetail.conn_id = _this.query.showConnPk;
      if (!_this.msgData[conn_id]) {
        this.table.body = [];
        return;
      }
      let body = [];
      _this.msgData[conn_id].map((item) => {
        if (_this.table.select_idx && _this.table.select_idx === item._id) {
          item._highlight = true;
        } else {
          item._highlight = false;
        }
        if (_this.isTableFilter(item)) {
          body.unshift(item);
        }
      });
      this.table.body = body;
    },
    refreshConnDetail: function () {
      let _this = this;
      _this.showConnDetail(_this.query.showConnPk);
    },
    search: function () {
      var el = event.currentTarget;
      if (!this.wsHandler.status) {
        el.style.setProperty("background", "#19be6b");
        this.webSocket();
      } else {
        if (this.wsHandler.status) {
          this.webSocket("disconnect");
        }
        el.style.setProperty("background", "#ed4014");
        return;
      }
    },
    clearScreen: function () {
      this.linkData = {};
      this.msgData = {};
      this.query.showConnPk = "";
      this.showMsgDetail = {
        pk: "",
        text: "",
        type: "",
        conn_id: "",
      };
      this.table.body = [];
    },
    showConn: function (row) {
      this.select_pk = row.pk;
      this.$emit("showConnDetail", row.pk);
    },
    utf8ToHex: function (string) {
      let hex_array = [];
      Array.from(string).map((ch) => {
        hex_array.push(
            ch.charCodeAt(0) < 128
                ? ch.charCodeAt(0).toString(16).padStart(2, "0").toUpperCase()
                : encodeURIComponent(ch).split("%").join(" ").trim("")
        );
      });
      return hex_array.join(" ");
    },
    updateHexText: function () {
      try {
        this.showMsgDetail.hex_text = this.utf8ToHex(this.showMsgDetail.text);
      } catch (e) {
        console.error(`无法进行编码, 错误: ${e}`);
        this.$Message.error(`无法进行编码, 错误: ${e}`);
      }
    },
    hexToArray: function (hex_string) {
      let text = [];
      for (let ch of hex_string) {
        if (ch === " ") {
          continue;
        }
        let last_str = text.length > 0 ? text[text.length - 1] : "";
        if (HEX_CH.includes(ch.toUpperCase())) {
          ch = ch.toUpperCase();
          if (last_str.length === 1) {
            text[text.length - 1] = `${last_str}${ch}`;
          } else {
            text.push(ch);
          }
        } else {
          this.$Message.error(`消息详情16进制编码有错误字符: ${ch}`);
          return [];
        }
      }
      return text;
    },
    updateText: function () {
      let hex_array = this.hexToArray(this.showMsgDetail.hex_text);
      if (!hex_array.length) {
        return;
      }
      this.showMsgDetail.hex_text = hex_array.join(" ");
      try {
        this.showMsgDetail.text = decodeURIComponent(`%${hex_array.join("%")}`);
      } catch (e) {
        console.error(`无法解码,错误: ${e}`);
      }
    },
    doAction: function (type) {
      let _this = this;
      let req = "";
      _this.msgDetail.actionStatus = true;
      try {
        if (type === "filter") {
          req = interceptImws(_this.showMsgDetail.conn_id, _this.msgDetail.filterStatus ? "off" : "on");
          _this.msgDetail.filterStatus = !_this.msgDetail.filterStatus;
        } else {
          req = interceptOpImws(
              _this.showMsgDetail.pk,
              _this.showMsgDetail.conn_id,
              type,
              _this.showMsgDetail.text
          );
        }
        req.then((resp) => {
          _this.msgDetail.actionStatus = false;
          if (type === "filter" && !_this.msgDetail.filterStatus) {
            return;
          }
          _this.$Message.info(`${_this.showMsgDetail.type}请求成功`);
          _this.showMsgDetail.pk = resp.data.data.data._id;
          _this.showMsgDetail.text = resp.data.data.data.content;
          _this.showMsgDetail.type = resp.data.data.data.direction;
        }).catch((err) => {
          _this.$Message.error(`${_this.showMsgDetail.type}请求失败`);
          console.error(err);
          if (type === "filter") {
            _this.msgDetail.filterStatus = !_this.msgDetail.filterStatus;
          }
          _this.msgDetail.actionStatus = false;
        });
      } catch (e) {
        _this.$Message.error(`${e}`);
        _this.msgDetail.actionStatus = false;
      }
    },
    repeaterGo: function (action) {
      let _this = this;
      _this.msgDetail.actionStatus = true;
      try {
        imwsRepeaterGo(
            _this.showMsgDetail.conn_id,
            _this.showMsgDetail.text,
            _this.showMsgDetail.hex_text.split(" ").join(""),
            action,
            _this.process_cnt
        )
            .then(() => {
              _this.$Message.info(`${action}请求成功`);
              _this.msgDetail.actionStatus = false;
            })
            .catch((err) => {
              _this.$Message.error(`${action}请求失败`);
              console.error(err);
              _this.msgDetail.actionStatus = false;
            });
      } catch (e) {
        _this.$Message.error(`${e}`);
        _this.msgDetail.actionStatus = false;
      }
    },
    showDetail: function (row) {
      this.table.select_idx = row._id;
      this.showMsgDetail = {
        pk: row._id,
        text: row.content,
        hex_text: this.utf8ToHex(row.content),
        type: row.direction,
        isShowHex: this.showMsgDetail.isShowHex,
        conn_id: row.conn_id,
      };
      this.table.body.map((item) => {
        item._highlight = false;
        if (row._id === item._id) {
          item._highlight = true;
        }
      });
    },
  }
}
</script>

<style scoped>
.ivu-btn-primary {
  background-color: #547EFF;
}
</style>