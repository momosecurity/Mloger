<template>
  <div class="layout">
    <Row style="margin: 10px">
      <Input
          v-model="query.client_ip"
          placeholder="IP"
          :style="{ margin: '0 10px ', 'width': '160px' }"
      />
      <Button
          type="error"
          class="search-btn"
          @click="search()"
          v-if="query.status === 'off'"
          :disabled="query.lock"
      >
        <Icon type="search"/>&nbsp;&nbsp;拦截已关闭
      </Button>
      <Button
          type="success"
          class="search-btn"
          :style="{ margin: '0 10px ' }"
          @click="search()"
          v-else
          :disabled="query.lock">
        <Icon type="search"/>&nbsp;&nbsp;拦截已开启
      </Button>
      <Button
          type="primary"
          class="search-btn"
          :style="{ margin: '0 10px' }"
          @click="updateData('forward')"
          :disabled="optQuery.lock">
        <Icon type="search"/>
        放过
      </Button>
      <Button
          type="primary"
          class="search-btn"
          :style="{ margin: '0 10px 0  0' }"
          @click="updateData('drop')"
          :disabled="optQuery.lock">
        <Icon type="search"/>
        丢弃
      </Button>
      <Button
          type="primary"
          class="search-btn"
          :style="{ margin: '0 10px 0 0' }"
          @click="optAtom"
          :disabled="optQuery.lock">
        <Icon type="search"/>
        重放
      </Button>
      <Checkbox v-model="optQuery.wait_response" size="large" :style="{ 'margin': '7px 20px','font-size':'14px' }">
        <span>等待响应</span>
      </Checkbox>
    </Row>
    <Row style="margin: 20px">
      <iCol span="24">
        <Card :bordered="true">
          <Input type="textarea" v-model="showContent" :autosize="{ minRows: 15 }"/>
        </Card>
      </iCol>
    </Row>
  </div>
</template>

<script>
import {getInterceptData, getInterceptOptData} from "@/utils/api";
import {showResponseData, showRequestData} from "@/utils/tools";

export default {
  name: "intercept-index",
  data() {
    return {
      query: {
        status: "off",
        client_ip: "",
        type: "",
        lock: false,
      },
      optQuery: {
        id: "",
        forward: false,
        drop: false,
        wait_response: false,
        type: "",
        flow_content: "",
        edited: false,
        lock: true,
      },
      showContent: "",
      showRawContent: "",
    }
  },
  methods: {
    updateData: function (type) {
      let _this = this;
      if (_this.optQuery.lock) {
        _this.$Notice.warning({
          title: "等待数据返回,请等待",
        });
        return;
      }
      _this.optQuery.lock = true;
      _this.optQuery.forward = type === "forward";
      _this.optQuery.drop = !_this.optQuery.forward;
      _this.optQuery.edited = _this.showContent !== _this.showRawContent;
      _this.optQuery.flow_content = btoa(encodeURI(_this.showContent));
      _this.showContent = "";
      getInterceptOptData(_this.optQuery)
          .then((resp) => {
            _this.setPageData(resp.data.data);
            _this.optQuery.lock = false;
          })
          .catch(function (err) {
            _this.optQuery.lock = false;
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
              _this.$Message.error(err);
            }
          });
    },
    search: function () {
      let _this = this;
      if (_this.query.lock) {
        _this.$Notice.warning({
          title: "等待数据返回,请等待",
        });
        return;
      }
      if (!_this.query.client_ip) {
        _this.$Notice.warning({
          title: "client ip不能为空",
        });
        return;
      }
      _this.query.status = _this.query.status === "on" ? "off" : "on";
      _this.optQuery.lock = true;
      _this.showContent = "";
      getInterceptData(_this.query, "post")
          .then((resp) => {
            _this.setPageData(resp.data.data);
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
              _this.$Message.error(err);
            }
          });
    },
    optAtom: function () {
      let pk = this.optQuery.id;
      if (!pk) {
        return "";
      }
      window.open("/#/repeater?id=" + pk);
    },
    setPageData: function (data) {
      let _this = this;
      if (data.type === "req") {
        _this.showContent = showRequestData(data.data);
      } else if (data.type === "res") {
        _this.showContent = showResponseData(data.data);
      } else {
        _this.showContent = "";
      }
      _this.showRawContent = _this.showContent;
      _this.query.client_ip = data.client_ip || _this.query.client_ip;
      _this.query.momoid = data.momoid || _this.query.momoid;
      _this.query.type = data.type || "";
      _this.query.status = data.status || _this.query.status;
      _this.optQuery.id = data.data._id || "";
      _this.optQuery.type = data.type || "";
      _this.optQuery.lock = !_this.optQuery.id;
    },
  },
  mounted() {
    if (this.$route.query.ip) {
      this.query.client_ip = this.$route.query.ip;
      return
    }
    getInterceptData()
        .then((resp) => {
          this.setPageData(resp.data.data);
          if (this.query.status !== "on") {
            return;
          }
          getInterceptData(this.query, "post")
              .then((resp) => {
                this.setPageData(resp.data.data);
              })
              .catch(function (err) {
                if (err.response) {
                  if (err.response.status < 500) {
                    this.$Notice.error({
                      title: "请求错误，注意检查请求参数",
                    });
                  } else {
                    this.$Notice.error({
                      title: "服务端发生未知错误,状态码: " + err.response.status,
                    });
                  }
                } else {
                  this.$Message.error(err);
                }
              });
        })
        .catch(function (err) {
          if (err.response) {
            if (err.response.status < 500) {
              this.$Notice.error({
                title: "请求错误，注意检查请求参数",
              });
            } else {
              this.$Notice.error({
                title: "服务端发生未知错误,状态码: " + err.response.status,
              });
            }
          } else {
            this.$Message.error(err);
          }
        });
  }
}
</script>

<style scoped>

</style>