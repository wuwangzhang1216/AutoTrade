'use client';

function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
var _excluded = ["size", "style"];
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(obj, key, value) { key = _toPropertyKey(key); if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : String(i); }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function _objectWithoutProperties(source, excluded) { if (source == null) return {}; var target = _objectWithoutPropertiesLoose(source, excluded); var key, i; if (Object.getOwnPropertySymbols) { var sourceSymbolKeys = Object.getOwnPropertySymbols(source); for (i = 0; i < sourceSymbolKeys.length; i++) { key = sourceSymbolKeys[i]; if (excluded.indexOf(key) >= 0) continue; if (!Object.prototype.propertyIsEnumerable.call(source, key)) continue; target[key] = source[key]; } } return target; }
function _objectWithoutPropertiesLoose(source, excluded) { if (source == null) return {}; var target = {}; var sourceKeys = Object.keys(source); var key, i; for (i = 0; i < sourceKeys.length; i++) { key = sourceKeys[i]; if (excluded.indexOf(key) >= 0) continue; target[key] = source[key]; } return target; }
import { memo } from 'react';
import { TITLE } from "../style";
import { jsx as _jsx } from "react/jsx-runtime";
import { jsxs as _jsxs } from "react/jsx-runtime";
var Icon = /*#__PURE__*/memo(function (_ref) {
  var _ref$size = _ref.size,
    size = _ref$size === void 0 ? '1em' : _ref$size,
    style = _ref.style,
    rest = _objectWithoutProperties(_ref, _excluded);
  return /*#__PURE__*/_jsxs("svg", _objectSpread(_objectSpread({
    fill: "currentColor",
    fillRule: "evenodd",
    height: size,
    style: _objectSpread({
      flex: 'none',
      lineHeight: 1
    }, style),
    viewBox: "0 0 24 24",
    width: size,
    xmlns: "http://www.w3.org/2000/svg"
  }, rest), {}, {
    children: [/*#__PURE__*/_jsx("title", {
      children: TITLE
    }), /*#__PURE__*/_jsx("path", {
      d: "M12.557 2.257a.432.432 0 00-.202-.366L9.42.063a.42.42 0 00-.444 0L3.601 3.395l-.022.015a.43.43 0 00-.18.352v3.443L.709 8.8a.43.43 0 00-.209.37v5.618a.43.43 0 00.214.343l2.685 1.56v3.512a.43.43 0 00.201.367l5.374 3.366a.42.42 0 00.442.002l2.935-1.79a.43.43 0 00.205-.369v-8.688h-.849v1.138L6.08 17.65l.436.737 5.191-3.156v6.305L9.2 23.066l-2.092-1.31 2.2-1.326-.434-.74-2.58 1.556-2.047-1.282v-3.406l2.374-1.43-.433-.739-2.476 1.493-2.363-1.373v-2.265l2.585-1.56-.434-.738-2.151 1.297V9.415l2.465-1.462 2.342 1.512v2.171l-1.75 1.15.461.72 1.67-1.095 1.533 1.088.486-.705-1.55-1.1v-2.27L9.56 7.817a.433.433 0 00.2-.366V4.728h-.848v2.483L6.55 8.7 4.247 7.216V4.003L6.12 2.84v2.712h.85V2.315L9.197.934l2.509 1.563v8.14h.85v-8.38z"
    }), /*#__PURE__*/_jsx("path", {
      clipRule: "evenodd",
      d: "M18.946 12.273a2.25 2.25 0 100-.818h-8.219v.818h8.22zm3.645-.41a1.432 1.432 0 11-2.863 0 1.432 1.432 0 012.863 0z"
    }), /*#__PURE__*/_jsx("path", {
      clipRule: "evenodd",
      d: "M18.091 14.727h-4.705v-.818h5.523V18h1.637v4.091h-4.091v-4.09h1.636v-3.274zm-.818 6.546v-2.455h2.454v2.455h-2.454z"
    }), /*#__PURE__*/_jsx("path", {
      clipRule: "evenodd",
      d: "M18.091 9h-4.705v.818h5.523v-4.09h2.375L18.5 1.273l-2.783 4.453h2.374V9zm.41-6.183L17.192 4.91h2.615L18.5 2.817z"
    })]
  }));
});
export default Icon;