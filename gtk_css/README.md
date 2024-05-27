# gtk_css

This is a silly **non-recommended**, **heavily incomplete** tool that can help you pretend
as if GTK exposed more properties over CSS, such as `hexpand` and `xalign`.

## Examples

### style.css
```css
frame#my-frame .wide-button {
    font-size: 120%;
    gtk-hexpand: true;
}
```

### application.ui
```xml
<object class="GtkOverlay">
  <object class="GtkFrame">
    <property name="name">my-frame</property>
    <child>
      <object class="GtkButton">
        <style>
          <class name="wide-button" />
        </style>
      </object>
    </child>
  </object>
</object>
```

`$ python3 -m gtk_css.main compile style.css application.ui /tmp`

### /tmp/style.css
```diff
frame#my-frame .wide-button {
    font-size: 120%;
-   gtk-hexpand: true;
}
```

### /tmp/application.ui
```diff
<object class="GtkOverlay">
  <object class="GtkFrame">
    <property name="name">my-frame</property>
    <child>
      <object class="GtkButton">
        <style>
          <class name="wide-button" />
        </style>
+       <property name="hexpand">true</property>
      </object>
    </child>
  </object>
</object>
```

The tool also supports the inverse operation, although this can result in very verbose
selectors:

`$ python3 -m gtk_css.main decompile /tmp/application.ui /tmp/de`

### /tmp/de/application.ui
```diff
<object class="GtkOverlay">
  <object class="GtkFrame">
    <property name="name">my-frame</property>
    <child>
      <object class="GtkButton">
        <style>
          <class name="wide-button" />
        </style>
-       <property name="hexpand">true</property>
      </object>
    </child>
  </object>
</object>
```

### /tmp/de/style.css
```diff
+ overlay frame#my-frame button.wide-button {
+     gtk-hexpand: true;
+ }
```

It can do slightly better if you provide a "compiled" CSS file to match against:

`$ python3 -m gtk_css.main decompile /tmp/style.css /tmp/application.ui /tmp/de`

### /tmp/de/style.css
```diff
frame#my-frame .wide-button {
    font-size: 120%;
+   gtk-hexpand: true;
}
```
