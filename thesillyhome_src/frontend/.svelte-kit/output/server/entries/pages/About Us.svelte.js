import { c as create_ssr_component, a as compute_rest_props, g as get_current_component, b as spread, d as escape_attribute_value, f as escape_object, h as add_attribute, v as validate_component } from "../../chunks/index-3c4e05aa.js";
import { f as forwardEventsBuilder, c as classMap, a as classAdderBuilder, D as Div, H as H5, b as H6, d as DefaultTabbar } from "../../chunks/classAdderBuilder-ba67c6d2.js";
import "@material/tab-bar";
import "@material/tab-scroller";
import "@material/dom";
import "@material/tab";
import "@material/ripple";
import "@material/tab-indicator";
const Paper = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "variant", "square", "color", "elevation", "transition", "getElement"]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { variant = "raised" } = $$props;
  let { square = false } = $$props;
  let { color = "default" } = $$props;
  let { elevation = 1 } = $$props;
  let { transition = false } = $$props;
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.variant === void 0 && $$bindings.variant && variant !== void 0)
    $$bindings.variant(variant);
  if ($$props.square === void 0 && $$bindings.square && square !== void 0)
    $$bindings.square(square);
  if ($$props.color === void 0 && $$bindings.color && color !== void 0)
    $$bindings.color(color);
  if ($$props.elevation === void 0 && $$bindings.elevation && elevation !== void 0)
    $$bindings.elevation(elevation);
  if ($$props.transition === void 0 && $$bindings.transition && transition !== void 0)
    $$bindings.transition(transition);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<div${spread([
    {
      class: escape_attribute_value(classMap({
        [className]: true,
        "smui-paper": true,
        "smui-paper--raised": variant === "raised",
        "smui-paper--unelevated": variant === "unelevated",
        "smui-paper--outlined": variant === "outlined",
        ["smui-paper--elevation-z" + elevation]: elevation !== 0 && variant === "raised",
        "smui-paper--rounded": !square,
        ["smui-paper--color-" + color]: color !== "default",
        "smui-paper-transition": transition
      }))
    },
    escape_object($$restProps)
  ], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</div>`;
});
var Content = classAdderBuilder({
  class: "smui-paper__content",
  component: Div
});
var Title = classAdderBuilder({
  class: "smui-paper__title",
  component: H5
});
var Subtitle = classAdderBuilder({
  class: "smui-paper__subtitle",
  component: H6
});
var About_Us_svelte_svelte_type_style_lang = "";
const css = {
  code: "div.svelte-ptzpgd{margin:25px 25px 25px 25px}",
  map: null
};
const Aboutu20Us = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  $$result.css.add(css);
  return `${validate_component(DefaultTabbar, "DefaultTabbar").$$render($$result, { active: "About Us" }, {}, {})}

<div class="${"paper-container svelte-ptzpgd"}">${validate_component(Paper, "Paper").$$render($$result, {}, {}, {
    default: () => {
      return `${validate_component(Title, "Title").$$render($$result, {}, {}, {
        default: () => {
          return `Support`;
        }
      })}
		${validate_component(Subtitle, "Subtitle").$$render($$result, {}, {}, {})}
		${validate_component(Content, "Content").$$render($$result, {}, {}, {
        default: () => {
          return `If you like this please visit us at
			<a href="${"https://thesillyhome.com/"}">The Silly Home</a>`;
        }
      })}`;
    }
  })}
</div>`;
});
export { Aboutu20Us as default };
