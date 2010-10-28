static enum test_result test_add_add_delay_add(ENGINE_HANDLE *h,
                                               ENGINE_HANDLE_V1 *h1) {
    add(h, h1);
    assertHasNoError(); // value is "0"
    add(h, h1);
    assertHasError(); // value is "0"
    delay(expiry+1);
    assertHasNoError(); // value is not defined
    add(h, h1);
    assertHasNoError(); // value is "0"
    checkValue(h, h1, "0");
    return SUCCESS;
}
