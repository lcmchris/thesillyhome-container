var __defProp = Object.defineProperty;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
import { t as noop, u as safe_not_equal, c as create_ssr_component, g as get_current_component, h as add_attribute, a as compute_rest_props, b as spread, d as escape_attribute_value, f as escape_object, v as validate_component, o as getContext, w as subscribe, s as setContext, q as onDestroy, x as set_store_value, y as compute_slots, e as escape, k as each } from "../../chunks/index-3c4e05aa.js";
import { f as forwardEventsBuilder, c as classMap, i as exclude, p as prefixFilter, d as DefaultTabbar } from "../../chunks/classAdderBuilder-ba67c6d2.js";
import { L as List, I as Item, G as Graphic, T as Text, P as PrimaryText, S as SecondaryText } from "../../chunks/index-4ca7f231.js";
import "@material/data-table";
import "@material/dom";
import "@material/tab-bar";
import "@material/tab-scroller";
import "@material/tab";
import "@material/ripple";
import "@material/tab-indicator";
import "@material/list";
const subscriber_queue = [];
function writable(value, start = noop) {
  let stop;
  const subscribers = /* @__PURE__ */ new Set();
  function set(new_value) {
    if (safe_not_equal(value, new_value)) {
      value = new_value;
      if (stop) {
        const run_queue = !subscriber_queue.length;
        for (const subscriber of subscribers) {
          subscriber[1]();
          subscriber_queue.push(subscriber, value);
        }
        if (run_queue) {
          for (let i = 0; i < subscriber_queue.length; i += 2) {
            subscriber_queue[i][0](subscriber_queue[i + 1]);
          }
          subscriber_queue.length = 0;
        }
      }
    }
  }
  function update(fn) {
    set(fn(value));
  }
  function subscribe2(run, invalidate = noop) {
    const subscriber = [run, invalidate];
    subscribers.add(subscriber);
    if (subscribers.size === 1) {
      stop = start(set) || noop;
    }
    run(value);
    return () => {
      subscribers.delete(subscriber);
      if (subscribers.size === 0) {
        stop();
        stop = null;
      }
    };
  }
  return { set, update, subscribe: subscribe2 };
}
const InnerGrid = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<div${add_attribute("class", classMap({
    [className]: true,
    "mdc-layout-grid__inner": true
  }), 0)}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</div>`;
});
const LayoutGrid = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "fixedColumnWidth", "align", "getElement"]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { fixedColumnWidth = false } = $$props;
  let { align = void 0 } = $$props;
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.fixedColumnWidth === void 0 && $$bindings.fixedColumnWidth && fixedColumnWidth !== void 0)
    $$bindings.fixedColumnWidth(fixedColumnWidth);
  if ($$props.align === void 0 && $$bindings.align && align !== void 0)
    $$bindings.align(align);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<div${spread([
    {
      class: escape_attribute_value(classMap({
        [className]: true,
        "mdc-layout-grid": true,
        "mdc-layout-grid--fixed-column-width": fixedColumnWidth,
        ["mdc-layout-grid--align-" + align]: align != null
      }))
    },
    escape_object(exclude($$restProps, ["innerGrid$"]))
  ], {})}${add_attribute("this", element, 0)}>${validate_component(InnerGrid, "InnerGrid").$$render($$result, Object.assign(prefixFilter($$restProps, "innerGrid$")), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}
</div>`;
});
const Cell$3 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "align", "order", "span", "spanDevices", "getElement"]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { align = void 0 } = $$props;
  let { order = void 0 } = $$props;
  let { span = void 0 } = $$props;
  let { spanDevices = {} } = $$props;
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.align === void 0 && $$bindings.align && align !== void 0)
    $$bindings.align(align);
  if ($$props.order === void 0 && $$bindings.order && order !== void 0)
    $$bindings.order(order);
  if ($$props.span === void 0 && $$bindings.span && span !== void 0)
    $$bindings.span(span);
  if ($$props.spanDevices === void 0 && $$bindings.spanDevices && spanDevices !== void 0)
    $$bindings.spanDevices(spanDevices);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<div${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-layout-grid__cell": true,
        ["mdc-layout-grid__cell--align-" + align]: align != null,
        ["mdc-layout-grid__cell--order-" + order]: order != null,
        ["mdc-layout-grid__cell--span-" + span]: span != null
      }, Object.fromEntries(Object.entries(spanDevices).map(([device, span2]) => [`mdc-layout-grid__cell--span-${span2}-${device}`, true])))))
    },
    escape_object($$restProps)
  ], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</div>`;
});
const Cell$2 = Cell$3;
const DataTable = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, [
    "use",
    "class",
    "stickyHeader",
    "sortable",
    "sort",
    "sortDirection",
    "sortAscendingAriaLabel",
    "sortDescendingAriaLabel",
    "container$use",
    "container$class",
    "table$use",
    "table$class",
    "layout",
    "getElement"
  ]);
  let $$slots = compute_slots(slots);
  let $progressClosed, $$unsubscribe_progressClosed;
  let $sortDirectionStore, $$unsubscribe_sortDirectionStore;
  let $sortStore, $$unsubscribe_sortStore;
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { stickyHeader = false } = $$props;
  let { sortable = false } = $$props;
  let { sort = null } = $$props;
  let { sortDirection = "ascending" } = $$props;
  let { sortAscendingAriaLabel = "sorted, ascending" } = $$props;
  let { sortDescendingAriaLabel = "sorted, descending" } = $$props;
  let { container$use = [] } = $$props;
  let { container$class = "" } = $$props;
  let { table$use = [] } = $$props;
  let { table$class = "" } = $$props;
  let element;
  let instance;
  let container;
  let internalClasses = {};
  let progressIndicatorStyles = { height: "auto", top: "initial" };
  let addLayoutListener = getContext("SMUI:addLayoutListener");
  let removeLayoutListener;
  let progressClosed = writable(false);
  $$unsubscribe_progressClosed = subscribe(progressClosed, (value) => $progressClosed = value);
  let sortStore = writable(sort);
  $$unsubscribe_sortStore = subscribe(sortStore, (value) => $sortStore = value);
  let sortDirectionStore = writable(sortDirection);
  $$unsubscribe_sortDirectionStore = subscribe(sortDirectionStore, (value) => $sortDirectionStore = value);
  setContext("SMUI:checkbox:context", "data-table");
  setContext("SMUI:linear-progress:context", "data-table");
  setContext("SMUI:linear-progress:closed", progressClosed);
  setContext("SMUI:data-table:sortable", sortable);
  setContext("SMUI:data-table:sort", sortStore);
  setContext("SMUI:data-table:sortDirection", sortDirectionStore);
  setContext("SMUI:data-table:sortAscendingAriaLabel", sortAscendingAriaLabel);
  setContext("SMUI:data-table:sortDescendingAriaLabel", sortDescendingAriaLabel);
  if (addLayoutListener) {
    removeLayoutListener = addLayoutListener(layout);
  }
  let previousProgressClosed = void 0;
  onDestroy(() => {
    if (removeLayoutListener) {
      removeLayoutListener();
    }
  });
  function layout() {
    return instance.layout();
  }
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.stickyHeader === void 0 && $$bindings.stickyHeader && stickyHeader !== void 0)
    $$bindings.stickyHeader(stickyHeader);
  if ($$props.sortable === void 0 && $$bindings.sortable && sortable !== void 0)
    $$bindings.sortable(sortable);
  if ($$props.sort === void 0 && $$bindings.sort && sort !== void 0)
    $$bindings.sort(sort);
  if ($$props.sortDirection === void 0 && $$bindings.sortDirection && sortDirection !== void 0)
    $$bindings.sortDirection(sortDirection);
  if ($$props.sortAscendingAriaLabel === void 0 && $$bindings.sortAscendingAriaLabel && sortAscendingAriaLabel !== void 0)
    $$bindings.sortAscendingAriaLabel(sortAscendingAriaLabel);
  if ($$props.sortDescendingAriaLabel === void 0 && $$bindings.sortDescendingAriaLabel && sortDescendingAriaLabel !== void 0)
    $$bindings.sortDescendingAriaLabel(sortDescendingAriaLabel);
  if ($$props.container$use === void 0 && $$bindings.container$use && container$use !== void 0)
    $$bindings.container$use(container$use);
  if ($$props.container$class === void 0 && $$bindings.container$class && container$class !== void 0)
    $$bindings.container$class(container$class);
  if ($$props.table$use === void 0 && $$bindings.table$use && table$use !== void 0)
    $$bindings.table$use(table$use);
  if ($$props.table$class === void 0 && $$bindings.table$class && table$class !== void 0)
    $$bindings.table$class(table$class);
  if ($$props.layout === void 0 && $$bindings.layout && layout !== void 0)
    $$bindings.layout(layout);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  set_store_value(sortStore, $sortStore = sort, $sortStore);
  set_store_value(sortDirectionStore, $sortDirectionStore = sortDirection, $sortDirectionStore);
  {
    if ($$slots.progress && instance && previousProgressClosed !== $progressClosed) {
      previousProgressClosed = $progressClosed;
      if ($progressClosed) {
        instance.hideProgress();
      } else {
        instance.showProgress();
      }
    }
  }
  $$unsubscribe_progressClosed();
  $$unsubscribe_sortDirectionStore();
  $$unsubscribe_sortStore();
  return `<div${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-data-table": true,
        "mdc-data-table--sticky-header": stickyHeader
      }, internalClasses)))
    },
    escape_object(exclude($$restProps, ["container$", "table$"]))
  ], {})}${add_attribute("this", element, 0)}><div${spread([
    {
      class: escape_attribute_value(classMap({
        [container$class]: true,
        "mdc-data-table__table-container": true
      }))
    },
    escape_object(prefixFilter($$restProps, "container$"))
  ], {})}${add_attribute("this", container, 0)}><table${spread([
    {
      class: escape_attribute_value(classMap({
        [table$class]: true,
        "mdc-data-table__table": true
      }))
    },
    escape_object(prefixFilter($$restProps, "table$"))
  ], {})}>${slots.default ? slots.default({}) : ``}</table></div>

  ${$$slots.progress ? `<div class="${"mdc-data-table__progress-indicator"}"${add_attribute("style", Object.entries(progressIndicatorStyles).map(([name, value]) => `${name}: ${value};`).join(" "), 0)}><div class="${"mdc-data-table__scrim"}"></div>
      ${slots.progress ? slots.progress({}) : ``}</div>` : ``}

  ${slots.paginate ? slots.paginate({}) : ``}
</div>`;
});
const Head$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let element;
  setContext("SMUI:data-table:row:header", true);
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<thead${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}</thead>`;
});
const Body$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "getElement"]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let element;
  setContext("SMUI:data-table:row:header", false);
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<tbody${spread([
    {
      class: escape_attribute_value(classMap({
        [className]: true,
        "mdc-data-table__content": true
      }))
    },
    escape_object($$restProps)
  ], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}</tbody>`;
});
let counter$1 = 0;
const Row$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "rowId", "getElement"]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { rowId = "SMUI-data-table-row-" + counter$1++ } = $$props;
  let element;
  let checkbox = void 0;
  let internalClasses = {};
  let internalAttrs = {};
  let header = getContext("SMUI:data-table:row:header");
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.rowId === void 0 && $$bindings.rowId && rowId !== void 0)
    $$bindings.rowId(rowId);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<tr${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-data-table__header-row": header,
        "mdc-data-table__row": !header,
        "mdc-data-table__row--selected": !header && checkbox && checkbox.checked
      }, internalClasses)))
    },
    {
      "aria-selected": escape_attribute_value(void 0)
    },
    escape_object(internalAttrs),
    escape_object($$restProps)
  ], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}</tr>`;
});
let counter = 0;
const Cell$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "numeric", "checkbox", "columnId", "sortable", "getElement"]);
  let $sort, $$unsubscribe_sort;
  let $sortDirection, $$unsubscribe_sortDirection;
  forwardEventsBuilder(get_current_component());
  let header = getContext("SMUI:data-table:row:header");
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { numeric = false } = $$props;
  let { checkbox = false } = $$props;
  let { columnId = header ? "SMUI-data-table-column-" + counter++ : "SMUI-data-table-unused" } = $$props;
  let { sortable = getContext("SMUI:data-table:sortable") } = $$props;
  let element;
  let internalClasses = {};
  let internalAttrs = {};
  let sort = getContext("SMUI:data-table:sort");
  $$unsubscribe_sort = subscribe(sort, (value) => $sort = value);
  let sortDirection = getContext("SMUI:data-table:sortDirection");
  $$unsubscribe_sortDirection = subscribe(sortDirection, (value) => $sortDirection = value);
  let sortAscendingAriaLabel = getContext("SMUI:data-table:sortAscendingAriaLabel");
  let sortDescendingAriaLabel = getContext("SMUI:data-table:sortDescendingAriaLabel");
  if (sortable) {
    setContext("SMUI:label:context", "data-table:sortable-header-cell");
    setContext("SMUI:icon-button:context", "data-table:sortable-header-cell");
    setContext("SMUI:icon-button:aria-describedby", columnId + "-status-label");
  }
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.numeric === void 0 && $$bindings.numeric && numeric !== void 0)
    $$bindings.numeric(numeric);
  if ($$props.checkbox === void 0 && $$bindings.checkbox && checkbox !== void 0)
    $$bindings.checkbox(checkbox);
  if ($$props.columnId === void 0 && $$bindings.columnId && columnId !== void 0)
    $$bindings.columnId(columnId);
  if ($$props.sortable === void 0 && $$bindings.sortable && sortable !== void 0)
    $$bindings.sortable(sortable);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  $$unsubscribe_sort();
  $$unsubscribe_sortDirection();
  return `${header ? `<th${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-data-table__header-cell": true,
        "mdc-data-table__header-cell--numeric": numeric,
        "mdc-data-table__header-cell--checkbox": checkbox,
        "mdc-data-table__header-cell--with-sort": sortable,
        "mdc-data-table__header-cell--sorted": sortable && $sort === columnId
      }, internalClasses)))
    },
    { role: "columnheader" },
    { scope: "col" },
    {
      "data-column-id": escape_attribute_value(columnId)
    },
    {
      "aria-sort": escape_attribute_value(sortable ? $sort === columnId ? $sortDirection : "none" : void 0)
    },
    escape_object(internalAttrs),
    escape_object($$restProps)
  ], {})}${add_attribute("this", element, 0)}>${sortable ? `
      <div class="${"mdc-data-table__header-cell-wrapper"}">${slots.default ? slots.default({}) : ``}
        <div class="${"mdc-data-table__sort-status-label"}" aria-hidden="${"true"}" id="${escape(columnId) + "-status-label"}">${escape($sort === columnId ? $sortDirection === "ascending" ? sortAscendingAriaLabel : sortDescendingAriaLabel : "")}</div></div>
    ` : `${slots.default ? slots.default({}) : ``}`}</th>` : `<td${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-data-table__cell": true,
        "mdc-data-table__cell--numeric": numeric,
        "mdc-data-table__cell--checkbox": checkbox
      }, internalClasses)))
    },
    escape_object(internalAttrs),
    escape_object($$restProps)
  ], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}</td>`}`;
});
const Head = Head$1;
const Body = Body$1;
const Row = Row$1;
const Cell = Cell$1;
var Dashboard_svelte_svelte_type_style_lang = "";
const css = {
  code: "input[type='checkbox'].svelte-h3jctr.svelte-h3jctr.svelte-h3jctr{display:none}.container.svelte-h3jctr img.svelte-h3jctr.svelte-h3jctr{margin:10px;transition:transform 0.25s ease;cursor:zoom-in}input[type='checkbox'].svelte-h3jctr:checked~label.svelte-h3jctr>img.svelte-h3jctr{transform:scale(2);cursor:zoom-out}",
  map: null
};
const Dashboard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { metrics } = $$props;
  let actuator = "No value";
  let accuracy = "Select the actuator";
  let precision = "		";
  let recall = "			";
  if ($$props.metrics === void 0 && $$bindings.metrics && metrics !== void 0)
    $$bindings.metrics(metrics);
  $$result.css.add(css);
  return `${validate_component(DefaultTabbar, "DefaultTabbar").$$render($$result, { active: "Dashboard" }, {}, {})}

${validate_component(LayoutGrid, "LayoutGrid").$$render($$result, {}, {}, {
    default: () => {
      return `${validate_component(Cell$2, "Cell").$$render($$result, {}, {}, {
        default: () => {
          return `${validate_component(List, "List").$$render($$result, {
            class: "act-list",
            twoLine: true,
            avatarList: true,
            singleSelection: true
          }, {}, {
            default: () => {
              return `${each(metrics, (metric) => {
                return `${validate_component(Item, "Item").$$render($$result, {
                  disabled: metric.disabled,
                  selected: actuator === metric.actuator
                }, {}, {
                  default: () => {
                    return `${validate_component(Graphic, "Graphic").$$render($$result, {
                      style: "background-image: url(/icons/light_icon.svg)"
                    }, {}, {})}
					${validate_component(Text, "Text").$$render($$result, {}, {}, {
                      default: () => {
                        return `${validate_component(PrimaryText, "PrimaryText").$$render($$result, {}, {}, {
                          default: () => {
                            return `${escape(metric.actuator)}`;
                          }
                        })}
						${validate_component(SecondaryText, "SecondaryText").$$render($$result, {}, {}, {
                          default: () => {
                            return `Accuracy = ${escape(metric.accuracy)}`;
                          }
                        })}
					`;
                      }
                    })}
				`;
                  }
                })}`;
              })}`;
            }
          })}`;
        }
      })}
	${validate_component(Cell$2, "Cell").$$render($$result, { align: "top" }, {}, {
        default: () => {
          return `${validate_component(DataTable, "DataTable").$$render($$result, {
            style: "border-style: solid; border-width: 1px; margin: 15px 15px 15px 15px;"
          }, {}, {
            default: () => {
              return `${validate_component(Head, "Head").$$render($$result, {}, {}, {
                default: () => {
                  return `${validate_component(Row, "Row").$$render($$result, {}, {}, {
                    default: () => {
                      return `${validate_component(Cell, "DataCell").$$render($$result, {}, {}, {
                        default: () => {
                          return `Metric`;
                        }
                      })}
					${validate_component(Cell, "DataCell").$$render($$result, {}, {}, {
                        default: () => {
                          return `Value`;
                        }
                      })}`;
                    }
                  })}`;
                }
              })}
			${validate_component(Body, "Body").$$render($$result, {}, {}, {
                default: () => {
                  return `${validate_component(Row, "Row").$$render($$result, {}, {}, {
                    default: () => {
                      return `${validate_component(Cell, "DataCell").$$render($$result, {}, {}, {
                        default: () => {
                          return `Accuracy`;
                        }
                      })}
					${validate_component(Cell, "DataCell").$$render($$result, { numeric: true }, {}, {
                        default: () => {
                          return `${escape(accuracy)}`;
                        }
                      })}`;
                    }
                  })}
				${validate_component(Row, "Row").$$render($$result, {}, {}, {
                    default: () => {
                      return `${validate_component(Cell, "DataCell").$$render($$result, {}, {}, {
                        default: () => {
                          return `Precision`;
                        }
                      })}
					${validate_component(Cell, "DataCell").$$render($$result, { numeric: true }, {}, {
                        default: () => {
                          return `${escape(precision)}`;
                        }
                      })}`;
                    }
                  })}
				${validate_component(Row, "Row").$$render($$result, {}, {}, {
                    default: () => {
                      return `${validate_component(Cell, "DataCell").$$render($$result, {}, {}, {
                        default: () => {
                          return `Recall`;
                        }
                      })}
					${validate_component(Cell, "DataCell").$$render($$result, { numeric: true }, {}, {
                        default: () => {
                          return `${escape(recall)}`;
                        }
                      })}`;
                    }
                  })}`;
                }
              })}`;
            }
          })}

		<div class="${"container svelte-h3jctr"}"><input type="${"checkbox"}" id="${"zoomCheck"}" class="${"svelte-h3jctr"}">
			${``}</div>`;
        }
      })}`;
    }
  })}`;
});
export { Dashboard as default };
