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
import { c as create_ssr_component, a as compute_rest_props, g as get_current_component, s as setContext, q as onDestroy, b as spread, d as escape_attribute_value, f as escape_object, h as add_attribute, v as validate_component, r as is_promise, t as noop, e as escape } from "../../chunks/index-3c4e05aa.js";
import { f as forwardEventsBuilder, c as classMap, a as classAdderBuilder, D as Div, e as H1, g as H2, d as DefaultTabbar } from "../../chunks/classAdderBuilder-ba67c6d2.js";
import "@material/ripple";
import "@material/dom";
import { MDCDismissibleDrawerFoundation, MDCModalDrawerFoundation } from "@material/drawer";
import { d as dispatch, L as List, I as Item, T as Text } from "../../chunks/index-4ca7f231.js";
import "@material/tab-bar";
import "@material/tab-scroller";
import "@material/tab";
import "@material/tab-indicator";
import "@material/list";
const Drawer = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "variant", "open", "fixed", "setOpen", "isOpen", "getElement"]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { variant = void 0 } = $$props;
  let { open = false } = $$props;
  let { fixed = true } = $$props;
  let element;
  let instance = void 0;
  let internalClasses = {};
  let previousFocus = null;
  let focusTrap;
  let scrim = false;
  setContext("SMUI:list:nav", true);
  setContext("SMUI:list:item:nav", true);
  setContext("SMUI:list:wrapFocus", true);
  let oldVariant = variant;
  onDestroy(() => {
    instance && instance.destroy();
    scrim && scrim.removeEventListener("SMUIDrawerScrim:click", handleScrimClick);
  });
  function getInstance() {
    var _a, _b;
    if (scrim) {
      scrim.removeEventListener("SMUIDrawerScrim:click", handleScrimClick);
    }
    if (variant === "modal") {
      scrim = (_b = (_a = element.parentNode) === null || _a === void 0 ? void 0 : _a.querySelector(".mdc-drawer-scrim")) !== null && _b !== void 0 ? _b : false;
      if (scrim) {
        scrim.addEventListener("SMUIDrawerScrim:click", handleScrimClick);
      }
    }
    const Foundation = variant === "dismissible" ? MDCDismissibleDrawerFoundation : variant === "modal" ? MDCModalDrawerFoundation : void 0;
    return Foundation ? new Foundation({
      addClass,
      removeClass,
      hasClass,
      elementHasClass: (element2, className2) => element2.classList.contains(className2),
      saveFocus: () => previousFocus = document.activeElement,
      restoreFocus: () => {
        if (previousFocus && "focus" in previousFocus && element.contains(document.activeElement)) {
          previousFocus.focus();
        }
      },
      focusActiveNavigationItem: () => {
        const activeNavItemEl = element.querySelector(".mdc-list-item--activated,.mdc-deprecated-list-item--activated");
        if (activeNavItemEl) {
          activeNavItemEl.focus();
        }
      },
      notifyClose: () => {
        open = false;
        dispatch(element, "SMUIDrawer:closed", void 0, void 0, true);
      },
      notifyOpen: () => {
        open = true;
        dispatch(element, "SMUIDrawer:opened", void 0, void 0, true);
      },
      trapFocus: () => focusTrap.trapFocus(),
      releaseFocus: () => focusTrap.releaseFocus()
    }) : void 0;
  }
  function hasClass(className2) {
    return className2 in internalClasses ? internalClasses[className2] : getElement().classList.contains(className2);
  }
  function addClass(className2) {
    if (!internalClasses[className2]) {
      internalClasses[className2] = true;
    }
  }
  function removeClass(className2) {
    if (!(className2 in internalClasses) || internalClasses[className2]) {
      internalClasses[className2] = false;
    }
  }
  function handleScrimClick() {
    instance && "handleScrimClick" in instance && instance.handleScrimClick();
  }
  function setOpen(value) {
    open = value;
  }
  function isOpen() {
    return open;
  }
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.variant === void 0 && $$bindings.variant && variant !== void 0)
    $$bindings.variant(variant);
  if ($$props.open === void 0 && $$bindings.open && open !== void 0)
    $$bindings.open(open);
  if ($$props.fixed === void 0 && $$bindings.fixed && fixed !== void 0)
    $$bindings.fixed(fixed);
  if ($$props.setOpen === void 0 && $$bindings.setOpen && setOpen !== void 0)
    $$bindings.setOpen(setOpen);
  if ($$props.isOpen === void 0 && $$bindings.isOpen && isOpen !== void 0)
    $$bindings.isOpen(isOpen);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  {
    if (oldVariant !== variant) {
      oldVariant = variant;
      instance && instance.destroy();
      internalClasses = {};
      instance = getInstance();
      instance && instance.init();
    }
  }
  {
    if (instance && instance.isOpen() !== open) {
      if (open) {
        instance.open();
      } else {
        instance.close();
      }
    }
  }
  return `<aside${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-drawer": true,
        "mdc-drawer--dismissible": variant === "dismissible",
        "mdc-drawer--modal": variant === "modal",
        "smui-drawer__absolute": variant === "modal" && !fixed
      }, internalClasses)))
    },
    escape_object($$restProps)
  ], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</aside>`;
});
var AppContent = classAdderBuilder({
  class: "mdc-drawer-app-content",
  component: Div
});
var Content = classAdderBuilder({
  class: "mdc-drawer__content",
  component: Div
});
classAdderBuilder({
  class: "mdc-drawer__header",
  component: Div
});
classAdderBuilder({
  class: "mdc-drawer__title",
  component: H1
});
classAdderBuilder({
  class: "mdc-drawer__subtitle",
  component: H2
});
var Controls_svelte_svelte_type_style_lang = "";
const css = {
  code: ".drawer-container.svelte-1ye5j9e{position:relative;display:flex;height:350px;border:1px solid var(--mdc-theme-text-hint-on-background, #ebac0e);overflow:hidden;z-index:0;margin:25px 25px 25px 25px}.svelte-1ye5j9e .app-content{flex:auto;position:relative;flex-grow:1}.main-content.svelte-1ye5j9e{overflow:auto;padding:16px;height:100%;box-sizing:border-box}",
  map: null
};
const Controls = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let script_output = "Not started";
  async function run_script(program, command) {
    const response = await fetch("/Controls", {
      method: "POST",
      headers: { accept: "application/json" },
      body: JSON.stringify({ program, command })
    });
    script_output = await response.text();
  }
  $$result.css.add(css);
  return `${validate_component(DefaultTabbar, "DefaultTabbar").$$render($$result, { active: "Controls" }, {}, {})}

<div class="${"drawer-container svelte-1ye5j9e"}">${validate_component(Drawer, "Drawer").$$render($$result, {}, {}, {
    default: () => {
      return `${validate_component(Content, "Content").$$render($$result, {}, {}, {
        default: () => {
          return `${validate_component(List, "List").$$render($$result, {}, {}, {
            default: () => {
              return `${validate_component(Item, "Item").$$render($$result, {
                href: "javascript:void(0)",
                style: "background-color: #EBAC0E; "
              }, {}, {
                default: () => {
                  return `${validate_component(Text, "Text").$$render($$result, { style: "color: #000000;" }, {}, {
                    default: () => {
                      return `Re-calibrate models`;
                    }
                  })}`;
                }
              })}`;
            }
          })}`;
        }
      })}`;
    }
  })}

	${validate_component(AppContent, "AppContent").$$render($$result, { class: "app-content" }, {}, {
    default: () => {
      return `<div class="${"main-content svelte-1ye5j9e"}">Console Output<br class="${"svelte-1ye5j9e"}">
			${function(__value) {
        if (is_promise(__value)) {
          __value.then(null, noop);
          return `
				<pre class="${"svelte-1ye5j9e"}">Loading...</pre>
			`;
        }
        return function() {
          return `
				<pre class="${"svelte-1ye5j9e"}">${escape(script_output)}</pre>
			`;
        }();
      }(run_script)}</div>`;
    }
  })}
</div>`;
});
export { Controls as default };
